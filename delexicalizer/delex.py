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
            else:
                f = filter(lambda tag: entity_map[tag].name == agent and 'AGENT' in tag, entity_map)
                if len(f) == 0:
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
            else:
                f = filter(lambda tag: entity_map[tag].name == patient, entity_map)
                if len(f) == 0:
                    tag = 'PATIENT-' + str(npatients)
                    entity_map[str(tag)] = dbop.get_entity(patient)
                    npatients += 1
        return entity_map, predicates

    def get_pronrefs(self, text, out_parse):
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

    def coreference_match(self, lexEntry, template, entity_map, out_parse):
        pronrefs = self.get_pronrefs(lexEntry.text, out_parse)

        for pronref in pronrefs:
            ranking = {}
            for tag in entity_map:
                ranking[tag] = []

                for nomref in pronref['nominalrefs']:
                    ranking[tag].append(edit_distance(entity_map[tag].name, nomref))
                ranking[tag] = np.mean(ranking[tag])

            ranking = sorted(ranking.items(), key=operator.itemgetter(1))
            tag = ranking[0][0]

            template = template.replace(' ' + pronref['reference'], ' '+tag, 1)
        return template

    def simple_match(self, lexEntry, template, entity_map):
        delex = []

        entities = sorted(entity_map.items(), key=lambda x: len(x[1]), reverse=True)
        for tag_entity in entities:
            tag, entity = tag_entity
            matcher = ' '.join(entity.name.replace('\'', '').replace('\"', '').split('_'))

            if len(re.findall(matcher, template)) > 0:
                template = template.replace(matcher, tag)

                reference = dbop.save_reference(tag, entity)
                dbop.add_reference(lexEntry, reference)
                delex.append(tag)

        return template, delex

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
                nps.append(parse_np(i))

        return nps

    def similarity_match(self, lexEntry, template, entity_map, delex_tag, nps):
        for tag, entity in entity_map.iteritems():
            if tag not in delex_tag:
                ranking = {}
                for np in nps:
                    ranking[np] = edit_distance(entity_map[tag].name, np)

                ranking = sorted(ranking.items(), key=operator.itemgetter(1))
                np = ranking[0][0]
                template = template.replace(np, tag)

                # TO DO: save reference np before delete it
                # nps.remove(np)

                reference = dbop.save_reference(tag, entity)
                dbop.add_reference(lexEntry, reference)

                delex_tag.append(tag)
        return template, delex_tag

    def process(self, entry):
        entity_map, predicates = self.parse(entry.triples)

        lexEntries = entry.texts
        for lexEntry in lexEntries:
            # stanford parsing
            out_parse = self.proc.parse_doc(lexEntry.text)

            # get template
            text = lexEntry.text
            if lexEntry.template == '':
                template = copy.copy(text)
            else:
                template = copy.copy(lexEntry.template)

            # Simple match
            template, delex_tags = self.simple_match(lexEntry, template, entity_map)

            if len(delex_tags) < len(entity_map):
                template, new_nps = self.normalize_dates(template, out_parse)

                nps = self.get_nps(lexEntry.parse_tree)
                nps.extend(new_nps)
                template, delex_tags = self.similarity_match(lexEntry, template, entity_map, delex_tags, nps)

            # Coreference match
            template = self.coreference_match(lexEntry, template, entity_map, out_parse)

            dbop.insert_template(lexEntry, template)

    def run(self):
        # entries = Entry.objects(size=2, category="Astronaut", set='train')
        entries = Entry.objects()

        print entries.count()
        for entry in entries:
            self.process(entry)
        evaluation.evaluate()

if __name__ == '__main__':
    dbop.clean_delex()
    Delexicalizer().run()