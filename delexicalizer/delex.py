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
import numpy as np
import operator
import re

class Delexicalizer(object):
    def __init__(self):
        self.proc = CoreNLP('coref')

        self.proc_parse = CoreNLP('parse')

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
                ranking[tag] = np.mean(ranking[tag])

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
    # REFERRING EXPRESSIONS PROCESSING
    # get reference details (syntactic position and referential status) and remove determiners and compounds
    def get_references(self, out, tag, entity):
        references = []
        removals = {}

        for i, snt in enumerate(out):
            deps = snt['deps_cc']
            visited_tokens = []
            for dep in deps:
                # get syntax
                if snt['tokens'][dep[2]] == tag and dep[2] not in visited_tokens:
                    visited_tokens.append(dep[2])
                    reference = {'syntax':'', 'sentence':i, 'pos':dep[2], 'entity':entity, 'tag':tag, 'determiner':'', 'compounds':[]}
                    if 'nsubj' in dep[0] or 'nsubjpass' in dep[0]:
                        reference['syntax'] = 'np-subj'
                    elif 'nmod:poss' in dep[0] or 'compound' in dep[0]:
                        reference['syntax'] = 'subj-det'
                    else:
                        reference['syntax'] = 'np-obj'
                    references.append(reference)

        for i, snt in enumerate(out):
            deps = snt['deps_cc']
            removals[i] = []
            for dep in deps:
                # mark compounds and determiners
                if snt['tokens'][dep[1]] == tag:
                    if dep[0] == 'det':
                        for j, reference in enumerate(references):
                            if reference['sentence'] == i and reference['pos'] == dep[1]:
                                references[j]['determiner'] = snt['tokens'][dep[2]].lower()
                                removals[i].append(dep[2])

                    if dep[0] == 'compound':
                        for j, reference in enumerate(references):
                            if reference['sentence'] == i and reference['pos'] == dep[1] \
                                    and 'AGENT' not in snt['tokens'][dep[2]] \
                                    and 'PATIENT' not in snt['tokens'][dep[2]] \
                                    and 'BRIDGE' not in snt['tokens'][dep[2]]:
                                references[j]['compounds'].append((dep[2], snt['tokens'][dep[2]]))
                                removals[i].append(dep[2])

        return references, removals

    # Parse and save references (referential status)
    def parse_references(self):
        self.references = sorted(self.references, key=lambda x: (x['entity'].name, x['sentence'], x['pos']))

        sentence_statuses = {}
        for i, reference in enumerate(self.references):
            if i == 0 or (reference['entity'].name != self.references[i-1]['entity'].name):
                reference['text_status'] = 'new'
            else:
                reference['text_status'] = 'given'

            if reference['entity'].name not in sentence_statuses:
                reference['sentence_status'] = 'new'
            else:
                reference['sentence_status'] = 'given'
            sentence_statuses[reference['entity'].name] = reference['sentence']

            ref = dbop.save_reference(entity=reference['entity'],
                                      syntax=reference['syntax'],
                                      text_status=reference['text_status'],
                                      sentence_status=reference['sentence_status'])

            refex = dbop.save_refex(reftype=reference['reftype'], refex=reference['refex'])
            dbop.add_refex(ref, refex)
    ############################################################################
    # Simple matching
    def simple_match(self, template, entity_map):
        delex = []
        refexes = {}

        entities = sorted(entity_map.items(), key=lambda x: len(x[1]), reverse=True)
        for tag_entity in entities:
            tag, entity = tag_entity
            matcher = ' '.join(entity.name.replace('\'', '').replace('\"', '').split('_'))

            if len(re.findall(matcher, template)) > 0:
                template = template.replace(matcher, 'SIMPLE-'+tag)
                refexes[entity.name] = matcher

                # Solving the bracket problem of regular expressions
                if len(re.findall(matcher, template)) == 0:
                    delex.append(tag)

        out = self.proc_parse.parse_doc(template)['sentences']
        removals = dict(map(lambda i: (i, []), range(len(out))))
        for tag_entity in entities:
            tag, entity = tag_entity
            references, entity_removals = self.get_references(out, 'SIMPLE-'+tag, entity)
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
                        normalized, text = root.attrib['value'], root.text

                        if re.match(regex, normalized) != None:
                            template = template.replace(text, normalized)
                            nps.append(normalized)
        return template, nps
    ############################################################################
    # Similarity match
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

    def similarity_match(self, template, entity_map, delex_tag, nps):
        refexes = {}

        for tag, entity in entity_map.iteritems():
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
            references, entity_removals = self.get_references(out, 'SIMILARITY-'+tag, entity)
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
                template = copy.copy(text)
            else:
                template = copy.copy(lexEntry.template)

            # Simple match
            template, delex_tags = self.simple_match(template, entity_map)

            if len(delex_tags) < len(entity_map):
                template, new_nps = self.normalize_dates(template, out_parse)

                # out = self.proc_parse.parse_doc(template)['sentences']
                # snt_templates = []
                nps = self.get_nps(lexEntry.parse_tree)
                nps.extend(new_nps)
                template, delex_tags = self.similarity_match(template, entity_map, delex_tags, nps)

            # Coreference match
            template = self.coreference_match(template, entity_map, out_parse)

            template = template.replace('SIMILARITY-', '').replace('SIMPLE-', '')
            dbop.insert_template(lexEntry, template)

            self.parse_references()

    def run(self):
        # entries = Entry.objects(set='train', docid='Id51', size=4, category='Building')
        entries = Entry.objects(set='train')

        print entries.count()
        for entry in entries:
            self.process(entry)
        evaluation.evaluate()

if __name__ == '__main__':
    dbop.clean_delex()
    Delexicalizer().run()