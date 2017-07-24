__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 03/05/2017
Description:
    Delexicalizing entities from the text based on the triples
    Methods: Coreference, Simple Match, Date Normalization and Similarity Match
"""

import sys
sys.path.append('../')
from db.model import *
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP
from nltk.metrics import edit_distance
import xml.etree.ElementTree as ET

import db.operations as dbop
import copy
import evaluation
import nltk
import numpy
import operator
import re
import reference_delex as ref_delex
import utils

class Delexicalizer(object):
    def __init__(self, _set='train', save_references=True):
        self._set = _set
        self.proc = CoreNLP('coref')

        self.proc_parse = CoreNLP('parse')

        self.e2f = utils.get_e2f('../data/lex.e2f')

        self.save_references = save_references
        # referring expressions per entity
        self.refexes = {}

    def parse(self, triples):
        entity_map, nagents, npatients, nbridges = {}, 1, 1, 1
        predicates = []
        for triple in triples:
            agent = triple.agent.name
            predicate = triple.predicate.name
            patient = triple.patient.name

            predicates.append(predicate)

            f = filter(lambda tag: entity_map[tag].name == agent and 'PATIENT' in tag, entity_map)
            if len(f) > 0:
                original_tag = f[0]
                original_id = int(original_tag.split('-')[1])
                new_tag = 'BRIDGE-' + str(nbridges)

                entity_map[str(new_tag)] = entity_map[str(original_tag)]
                del entity_map[str(original_tag)]

                nbridges += 1
                new_entity_map = {}
                for tag in entity_map.keys():
                    role, id = tag.split('-')
                    id = int(id)
                    if role == 'PATIENT' and id > original_id:
                        new_entity_map[role+'-'+str(id-1)] = entity_map[str(tag)]
                    else:
                        new_entity_map[str(tag)] = entity_map[str(tag)]
                entity_map = copy.deepcopy(new_entity_map)
                npatients -= 1
            elif agent not in map(lambda entity: entity.name, entity_map.values()):
                tag = 'AGENT-' + str(nagents)
                entity_map[str(tag)] = dbop.get_entity(agent)
                nagents += 1

            f = filter(lambda tag: entity_map[tag].name == patient and 'AGENT' in tag, entity_map)
            if len(f) > 0:
                original_tag = f[0]
                original_id = int(original_tag.split('-')[1])
                new_tag = 'BRIDGE-' + str(nbridges)

                entity_map[str(new_tag)] = entity_map[str(original_tag)]
                del entity_map[str(original_tag)]

                nbridges += 1
                new_entity_map = {}
                for tag in entity_map.keys():
                    role, id = tag.split('-')
                    id = int(id)
                    if role == 'AGENT' and id > original_id:
                        new_entity_map[role+'-'+str(id-1)] = entity_map[str(tag)]
                    else:
                        new_entity_map[str(tag)] = entity_map[str(tag)]
                entity_map = copy.deepcopy(new_entity_map)
                nagents -= 1
            elif patient not in map(lambda entity: entity.name, entity_map.values()):
                tag = 'PATIENT-' + str(npatients)
                entity_map[str(tag)] = dbop.get_entity(patient)
                npatients += 1

        return entity_map, predicates
    ############################################################################
    # COREFERENCE MATCH
    def get_pronrefs(self, out_parse):
        # pronominal references
        pronrefs = []

        # select only entities with coreferences
        coreferences = filter(lambda entity: len(entity['mentions']) > 1, out_parse['entities'])
        # Get all the pronominal references and attach the nominal reference to it
        for entity in coreferences:
            nominalrefs = []
            entity_pronouns = []
            for mention in entity['mentions']:
                # get reference in the tokenized sentence
                snt = mention['sentence']
                begin, end = mention['tokspan_in_sentence']
                reference = ' '.join(out_parse['sentences'][snt]['tokens'][begin:end])

                if mention['mentiontype'] == 'PRONOMINAL':
                    # save pronominal reference of the entity
                    pronoun = {'reference':reference, 'sentence':snt, 'pos':begin}
                    entity_pronouns.append(pronoun)
                else:
                    # save nominal references of the entity
                    nominalrefs.append(reference)

            for pronominal in entity_pronouns:
                pronominal['nominalrefs'] = nominalrefs
            pronrefs.extend(entity_pronouns)

        # Sort similar pronominal references by their order in the text
        return sorted(pronrefs, key=lambda x: (x['sentence'], x['pos']))

    def coreference_match(self, template, entity_map, out_parse):
        pronrefs = self.get_pronrefs(out_parse)

        for pronref in pronrefs:
            ranking = {}
            for tag in entity_map:
                ranking[tag] = []

                for nomref in pronref['nominalrefs']:
                    ranking[tag].append(edit_distance(entity_map[tag].name, nomref))
                ranking[tag] = numpy.mean(ranking[tag])

            ranking = sorted(ranking.items(), key=operator.itemgetter(1))
            tag = ranking[0][0]

            template = template.replace(' ' + pronref['reference'], ' PRON-'+tag, 1)

            out = self.proc_parse.parse_doc(template)['sentences']
            references, removals = self.get_references(out, 'PRON-'+tag, entity_map[tag])
            for reference in references:
                reference['tag'] = tag
                reference['reftype'] = 'pronoun'
                reference['refex'] = pronref['reference'].lower()
            self.references.extend(references)

            # Remove marked tokens
            snt_templates = len(out) * ['']
            for i, snt in enumerate(out):
                snt_template = []
                for j, token in enumerate(snt['tokens']):
                    if j not in removals[i]:
                        snt_template.append(token)
                snt_templates[i] = ' '.join(snt_template)

            template = ' '.join(snt_templates).replace('-LRB- ', '(').replace(' -RRB-', ')').replace('-LRB-', '(').replace('-RRB-', ')').strip()
            template = template.replace('PRON-', '')

        return template
    ############################################################################

    ############################################################################
    # Simple matching
    def simple_match(self, template, entity_map):
        delex = []
        refexes = {}

        entities = sorted(entity_map.items(), key=lambda x: len(x[1].name), reverse=True)
        for tag_entity in entities:
            tag, entity = tag_entity
            matcher = ' '.join(entity.name.replace('\'', '').replace('\"', '').split('_'))
            matcher = ' '.join(nltk.word_tokenize(matcher)) + ' '

            if len(re.findall(matcher, template)) > 0:
                template = template.replace(matcher, 'SIMPLE-'+tag+' ')
                refexes[entity.name] = matcher

                # Solving the bracket problem of regular expressions
                if len(re.findall(matcher, template)) == 0:
                    delex.append(tag)

        out = self.proc_parse.parse_doc(template)['sentences']
        removals = dict(map(lambda i: (i, []), range(len(out))))
        for tag_entity in entities:
            tag, entity = tag_entity
            references, entity_removals = ref_delex.get_references(out, 'SIMPLE-'+tag, entity)
            for reference in references:
                reference['tag'] = tag
                reference['reftype'] = 'name'

                reference['refex'] = reference['determiner']
                for compound in sorted(reference['compounds'], key=lambda x: x[0]):
                    reference['refex'] = reference['refex'] + ' ' + compound[1]
                reference['refex'] = reference['refex'] + ' ' + refexes[entity.name]

                del reference['determiner']
                del reference['compounds']
            self.references.extend(references)

            for k in entity_removals:
                removals[k].extend(entity_removals[k])

        # Remove marked tokens
        snt_templates = len(out) * ['']
        for i, snt in enumerate(out):
            snt_template = []
            for j, token in enumerate(snt['tokens']):
                if j not in removals[i]:
                    snt_template.append(token)
            snt_templates[i] = ' '.join(snt_template)

        template = ' '.join(snt_templates).replace('-LRB- ', '(').replace(' -RRB-', ')').replace('-LRB-', '(').replace('-RRB-', ')').strip()
        return template, delex
    ############################################################################

    def normalize_dates(self, template, out_parse):
        regex = '[0-9]{4}-[0-9]{2}-[0-9]{2}'

        nps = []

        for snt in out_parse['sentences']:
            for mention in snt['entitymentions']:
                if mention['type'] == 'DATE' and 'timex_xml' in mention:
                    root = ET.fromstring(mention['timex_xml'])
                    if 'value' in root.attrib:
                        normalized, text = root.attrib['value'], ' '.join(nltk.word_tokenize(root.text))

                        if re.match(regex, normalized) != None:
                            template = template.replace(text, normalized)
                            nps.append(normalized)
        return template, nps
    ############################################################################
    # Similarity and probabilist matches match
    def get_nps(self, tree):
        def parse_np(index):
            np = ''
            closing = 0
            for elem in tree[index:]:
                if elem[0] == '(':
                    closing += 1
                else:
                    match = re.findall("\)", elem)

                    np += elem.replace(')', '').strip() + ' '

                    closing -= len(match)
                    if closing <= 0:
                        break
            return np.replace('-LRB- ', '(').replace(' -RRB-', ')').replace('-LRB-', '(').replace('-RRB-', ')').strip()

        nps = []
        tree = tree.split()
        for i, elem in enumerate(tree):
            if elem == '(NP':
                np = parse_np(i)
                if 'AGENT' not in np and 'PATIENT' not in np and 'BRIDGE' not in np:
                    nps.append(np)
        return nps

    def probabilistic_match(self, template, entity_map, predicates, nps):
        def calc_prob(np, wiki):
            words = np.split()

            if wiki not in self.e2f:
                return None

            _min = numpy.log(sys.float_info.min)
            prob = 0
            for word in words:
                if word in self.e2f[wiki]:
                    prob += numpy.log(self.e2f[wiki][word])
                else:
                    prob += _min
            return prob

        refexes = {}
        while len(nps) > 0:
            np = nps[0]
            if np in template:
                ranking = {}
                for tag, entity in entity_map.items():
                    prob = calc_prob(np.lower(), entity_map[tag].name.lower())
                    if prob != None:
                        ranking[tag] = prob

                for predicate in predicates:
                    prob = calc_prob(np.lower(), predicate.lower())
                    if prob != None:
                        ranking[predicate] = prob

                ranking = sorted(ranking.items(), key=operator.itemgetter(1), reverse=True)

                tag = ranking[0][0]
                if tag not in predicates:
                    template = template.replace(np, 'PROBABILISTIC-'+tag)
                    entity = entity_map[tag]
                    refexes[entity.name] = np

            del nps[0]

        out = self.proc_parse.parse_doc(template)['sentences']
        removals = dict(map(lambda i: (i, []), range(len(out))))
        for tag, entity in entity_map.iteritems():
            references, entity_removals = ref_delex.get_references(out, 'PROBABILISTIC-'+tag, entity)
            for reference in references:
                reference['tag'] = tag
                reference['reftype'] = 'name'
                reference['refex'] = refexes[entity.name]

                del reference['determiner']
                del reference['compounds']
            self.references.extend(references)

            for k in entity_removals:
                removals[k].extend(entity_removals[k])

        # Remove marked tokens
        snt_templates = len(out) * ['']
        for i, snt in enumerate(out):
            snt_template = []
            for j, token in enumerate(snt['tokens']):
                if j not in removals[i]:
                    snt_template.append(token)
            snt_templates[i] = ' '.join(snt_template)

        template = ' '.join(snt_templates).replace('-LRB- ', '(').replace(' -RRB-', ')').replace('-LRB-', '(').replace('-RRB-', ')').strip()

        return template

    def similarity_match(self, template, entity_map, delex_tag, nps):
        refexes = {}

        entities = sorted(entity_map.items(), key=lambda x: len(x[1].name), reverse=True)
        for tag, entity in entities:
            if tag not in delex_tag:
                ranking = {}
                for np in nps:
                    ranking[np] = edit_distance(' '.join(entity_map[tag].name.split('_')), np)

                ranking = sorted(ranking.items(), key=operator.itemgetter(1))
                np = ranking[0][0]
                template = template.replace(np, 'SIMILARITY-'+tag)
                refexes[entity.name] = np

                delex_tag.append(tag)

        out = self.proc_parse.parse_doc(template)['sentences']
        removals = dict(map(lambda i: (i, []), range(len(out))))
        for tag, entity in entity_map.iteritems():
            references, entity_removals = ref_delex.get_references(out, 'SIMILARITY-'+tag, entity)
            for reference in references:
                reference['tag'] = tag
                reference['reftype'] = 'name'
                reference['refex'] = refexes[entity.name]

                del reference['determiner']
                del reference['compounds']
            self.references.extend(references)

            for k in entity_removals:
                removals[k].extend(entity_removals[k])

        # Remove marked tokens
        snt_templates = len(out) * ['']
        for i, snt in enumerate(out):
            snt_template = []
            for j, token in enumerate(snt['tokens']):
                if j not in removals[i]:
                    snt_template.append(token)
            snt_templates[i] = ' '.join(snt_template)

        template = ' '.join(snt_templates).replace('-LRB- ', '(').replace(' -RRB-', ')').replace('-LRB-', '(').replace('-RRB-', ')').strip()

        return template, delex_tag
    ############################################################################

    def process(self, entry):
        entity_map, predicates = self.parse(entry.triples)
        lexEntries = entry.texts
        for lexEntry in lexEntries:
            self.references = []

            # stanford parsing
            out_parse = self.proc.parse_doc(lexEntry.text)
            self.out_parse = out_parse

            # get template
            text = lexEntry.text
            if lexEntry.template == '':
                template = []
                for snt in self.out_parse['sentences']:
                    template.append(' '.join(snt['tokens']))
                template = ' '.join(template).replace('-LRB-', '(').replace('-RRB-', ')').strip()
            else:
                template = copy.copy(lexEntry.template)

            # Simple match
            template, delex_tags = self.simple_match(template, entity_map)

            # Similarity matching (only for date matching from now on)
            if len(delex_tags) < len(entity_map):
                template, new_nps = self.normalize_dates(template, self.out_parse)

                out = self.proc_parse.parse_doc(template)
                parse_trees = []
                for snt in out['sentences']:
                    parse_trees.append(snt['parse'])

                if len(parse_trees) > 1:
                    parse_tree = '(MULTI-SENTENCE '
                    for tree in parse_trees:
                        parse_tree += tree + ' '
                    parse_tree = parse_tree.strip() + ')'
                else:
                    parse_tree = parse_trees[0]

                nps = self.get_nps(parse_tree)
                nps.extend(new_nps)
                if len(nps) > 0:
                    template, delex_tags = self.similarity_match(template, entity_map, delex_tags, nps)

            # Probabilistic matching
            # nps = self.get_nps(parse_tree)
            # template = self.probabilistic_match(template, entity_map, predicates, nps)

            # Coreference match
            template = self.coreference_match(template, entity_map, self.out_parse)

            template = template.replace('SIMILARITY-', '').replace('SIMPLE-', '').replace('PROBABILISTIC-', '')
            dbop.insert_template(lexEntry, template)

            print text
            print template
            print 10 * '-'

            if self.save_references:
                ref_delex.parse_references(self.references)

    def run(self):
        # entries = Entry.objects(set='train', size=1)
        entries = Entry.objects(set=self._set)

        print entries.count()
        for entry in entries:
            self.process(entry)
        evaluation.evaluate()

if __name__ == '__main__':
    dbop.clean_delex()
    Delexicalizer(_set='train', save_references=True).run()
    Delexicalizer(_set='dev', save_references=False).run()