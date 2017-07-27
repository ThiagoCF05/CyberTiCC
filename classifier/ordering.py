__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 15/06/2017
Description:
    Sentence segmentation and discourse ordering
"""

import copy
import json
import re
import sys
sys.path.append('../')
from db.model import *
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP
import db.operations as dbop
import utils

class Ordering(object):
    def __init__(self):
        self.proc = CoreNLP('ssplit')

    def check_tagfrequency(self, entitymap, template):
        tag_freq = {}
        for tag, entity in entitymap.items():
            tag_freq[tag] = re.findall(tag, template)

        if 0 not in tag_freq.values():
            return True
        return False

    # Fixing the tags for the correct order
    def generate_template(self, triples, template, entitymap):
        '''
        :param triples:
        :param template:
        :param entitymap:
        :return:
        '''
        new_entitymap, predicates = utils.map_entities(triples)
        new_entitymap = dict(map(lambda x: (x[1].name, x[0]), new_entitymap.items()))
        new_template = []
        for token in template:
            if token in entitymap:
                new_template.append(new_entitymap[entitymap[token].name])
            else:
                new_template.append(token)
        return ' '.join(new_template).replace('-LRB-', '(').replace('-RRB-', ')').strip()

    def process(self, entry):
        '''
        :param entry:
        :return:
        '''
        self.entry = entry
        entitymap, predicates = utils.map_entities(self.entry.triples)

        training_set = []
        for lex in self.entry.texts:
            template = lex.template
            delex_type = lex.delex_type

            if self.check_tagfrequency(entitymap, template):
                sort_triples, triples = [], copy.deepcopy(entry.triples)
                out = self.proc.parse_doc(template)

                prev_tags = []
                for i, snt in enumerate(out['sentences']):
                    tags = []

                    # get tags in order
                    for token in snt['tokens']:
                        if token in entitymap:
                            tags.append(token)

                    # Ordering the triples in the sentence i
                    sort_snt_triples, triples = self.order(triples, entitymap, prev_tags, tags)
                    sort_triples.extend(sort_snt_triples)

                # Extract template for the sentence
                if len(triples) == 0:
                    template = []
                    for snt in out['sentences']:
                        template.extend(snt['tokens'])
                    template = self.generate_template(sort_triples, template, entitymap)
                    training_set.append({'sorted_triples':sort_triples, 'triples':entry.triples, 'template':template, 'lexEntry':lex, 'semcategory':entry.category, 'delex_type':delex_type})
        return training_set

    def order(self, triples, entitymap, prev_tags, tags):
        triples_sorted = []
        for i in range(1, len(tags)):
            tag = tags[i]
            prev_tags.insert(0, tags[i-1])

            for prev_tag in prev_tags:
                if 'AGENT' in tag and 'PATIENT' in prev_tag:
                    f = filter(lambda triple: triple.agent.name == entitymap[tag].name and triple.patient.name == entitymap[prev_tag].name, triples)
                elif 'PATIENT' in tag and 'AGENT' in prev_tag:
                    f = filter(lambda triple: triple.patient.name == entitymap[tag].name and triple.agent.name == entitymap[prev_tag].name, triples)
                else:
                    f = filter(lambda triple: (triple.agent.name == entitymap[tag].name and triple.patient.name == entitymap[prev_tag].name) or
                                              (triple.patient.name == entitymap[tag].name and triple.agent.name == entitymap[prev_tag].name), triples)

                if len(f) > 0:
                    triples_sorted.append(f[0])
                    triples = filter(lambda triple: triple != f[0], triples)
                    break
        return triples_sorted, triples

    def update_db(self, trainingset):
        '''
        :param trainingset: set with triples, ordered triples, lexical entry and updateded template
        :return:
        '''
        for row in trainingset:
            # Update database with template with right entity order id and ordered triples
            dbop.save_template(category=row['semcategory'], triples=row['sorted_triples'], template=row['template'], delex_type=row['delex_type'])

    def write(self, trainingset, fname):
        result = []

        for row in trainingset:
            lex, triples, sorted_triples, template = row['lexEntry'], row['triples'], row['sorted_triples'], row['template']

            row['triples'] = map(lambda triple: triple.agent.name + ' | ' + triple.predicate.name + ' | ' + triple.patient.name, row['triples'])
            row['sorted_triples'] = map(lambda triple: triple.agent.name + ' | ' + triple.predicate.name + ' | ' + triple.patient.name, row['sorted_triples'])
            result.append({'triples':row['triples'], 'sorted':row['sorted_triples'], 'semcategory':row['semcategory']})

            print row['triples']
            print row['sorted_triples']
            print template
            print 10 * '-'

        json.dump(result, open(fname, 'w'), indent=4, separators=(',', ': '))

if __name__ == '__main__':
    ordering = Ordering()

    training = []
    entries = Entry.objects(set='train')
    # entries = Entry.objects(set='train', size=1)

    for entry in entries:
        result = ordering.process(entry)
        training.extend(result)

    ordering.update_db(training)
    ordering.write(training, 'data/train_order.json')

    dev = []
    entries = Entry.objects(set='dev')

    for entry in entries:
        result = ordering.process(entry)
        dev.extend(result)

    # ordering.update_db(dev)
    ordering.write(dev, 'data/dev_order.json')