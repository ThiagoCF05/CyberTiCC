__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 22/06/2017
Description:
    Simple natural language generation system which retrieves text templates
    based on the order of the predicates
"""

import argparse
import copy
import sys
sys.path.append('../')
from db.model import *
import kenlm
import nltk
import operator
import utils

from reg.reg_main import REG

class CyberNLG(object):
    def __init__(self, lm_path, beam):
        self.references = []
        self.hyps = []

        self.beam = beam

        self.reg = REG()
        self.model = kenlm.Model(lm_path)

        deventries = Entry.objects(set='dev').timeout(False)
        for deventry in deventries:
            self.process(deventry)

    def extract_template(self, triples):
        # entity and predicate mapping
        entitymap, predicates = utils.map_entities(triples=triples)

        train_templates = Template.objects(triples__size=len(triples))
        for i, triple in enumerate(triples):
            train_templates = filter(lambda template: template.triples[i].predicate.name == triple.predicate.name, train_templates)

        # extract templates
        templates = []
        for entry in train_templates:
            template = entry.template

            entitiesPresence = True
            for tag in entitymap:
                if tag not in template:
                    entitiesPresence = False
                    break
            if entitiesPresence:
                templates.append(template)

        templates = nltk.FreqDist(templates)
        templates = sorted(templates.items(), key=operator.itemgetter(1), reverse=True)

        new_templates = []
        dem = sum(map(lambda item: item[1], templates))
        for item in templates:
            template, freq = item
            # REPLACE ENTITY TAGS FOR WIKIPEDIA IDs
            for tag, entity in sorted(entitymap.items(), key=lambda x: len(x[1].name), reverse=True):
                template = template.replace(tag, '_'.join(entity.name.replace('\'', '').replace('\"', '').split()))
            new_templates.append((template, float(freq)/dem))

        return new_templates, entitymap, predicates

    def get_new_entitymap(self, entitymap):
        new_entitymap = {}

        tags = sorted(entitymap.keys())
        for i, tag in enumerate(tags):
            new_tag = 'ENTITY-' + str(i+1)
            new_entitymap[entitymap[tag]] = new_tag
        return new_entitymap

    def reg_process(self, templates, entitymap):
        new_templates = []
        for item in templates:
            template, freq = item

            # Replace WIKI-IDS for simple tags (ENTITY-1, etc). In order to make it easier for the parser
            new_entitymap = self.get_new_entitymap(entitymap)
            for entity, tag in sorted(new_entitymap.items(), key=lambda x: len(x[0].name), reverse=True):
                name = '_'.join(entity.name.replace('\'', '').replace('\"', '').split())
                template = template.replace(name, tag)

            # Generating referring expressions
            new_entitymap = dict(map(lambda x: (x[1], x[0]), new_entitymap.items()))
            template = self.reg.generate(template, new_entitymap)
            new_templates.append(template)
        return new_templates

    def process(self, deventry):
        print 10 * '-'
        print 'ID:', str(deventry.docid), str(deventry.size), str(deventry.category)

        # extract references
        refs = []
        for lexEntry in deventry.texts:
            text = lexEntry.text
            refs.append(text)
        self.references.append(refs)

        # Try to extract a full template
        # TO DO: ordering triples
        triples = deventry.triples
        begin, end, templates = 0, len(triples), []
        while begin != end:
            partial_templates, entitymap, predicates = self.extract_template(triples[begin:end])[:self.beam]

            if len(partial_templates) > 0:
                if len(templates) == 0:
                    templates = map(lambda template: ([template[0]], template[1]), partial_templates)
                else:
                    for i, template in enumerate(templates):
                        for partial_template in partial_templates:
                            templates[i][0].append(partial_template[0])
                            templates[i] = (templates[i][0], templates[i][1] * partial_template[1])

                    templates = sorted(templates, key=lambda template: template[1], reverse=True)[:self.beam]

                    begin = copy.copy(end)
                    end = len(triples)
            else:
                end -= 1

        entitymap, predicates = utils.map_entities(deventry.triples)
        templates = self.reg_process(templates, entitymap)

        # Ranking with KenLM
        template = sorted(templates, key=lambda x: self.model.score(x), reverse=True)[0]

        self.hyps.append(template.strip())

        print 'Entities: ', str(map(lambda x: (x[0], x[1].name), entitymap.items()))
        print 'Predicate: ', str(map(lambda predicate: predicate.name, predicates))
        print template.encode('utf-8')
        print 10 * '-'
        return template

def write_references(refs, fname):
    f1 = open(fname+'1', 'w')
    f2 = open(fname+'2', 'w')
    f3 = open(fname+'3', 'w')
    f4 = open(fname+'4', 'w')
    f5 = open(fname+'5', 'w')
    f6 = open(fname+'6', 'w')
    f7 = open(fname+'7', 'w')

    for references in refs:
        f1.write(references[0].encode('utf-8'))
        f1.write('\n')

        if len(references) >= 2:
            f2.write(references[1].encode('utf-8'))
        f2.write('\n')

        if len(references) >= 3:
            f3.write(references[2].encode('utf-8'))
        f3.write('\n')

        if len(references) >= 4:
            f4.write(references[3].encode('utf-8'))
        f4.write('\n')

        if len(references) >= 5:
            f5.write(references[4].encode('utf-8'))
        f5.write('\n')

        if len(references) >= 6:
            f6.write(references[5].encode('utf-8'))
        f6.write('\n')

        if len(references) >= 7:
            f7.write(references[6].encode('utf-8'))
        f7.write('\n')

    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()
    f6.close()
    f7.close()

def write_hyps(hyps, fname):
    f = open(fname, 'w')
    for hyp in hyps:
        f.write(hyp.encode('utf-8'))
        f.write('\n')
    f.close()

if __name__ == '__main__':
    # python simplenlg.py /home/tcastrof/cyber/data/easy_nlg/hyps /home/tcastrof/cyber/data/easy_nlg/ref
    parser = argparse.ArgumentParser()
    parser.add_argument('hyps', type=str, default='/home/tcastrof/cyber/data/easy_nlg/hyps', help='hypothesis writing file')
    parser.add_argument('refs', type=str, default='/home/tcastrof/cyber/data/easy_nlg/ref', help='references writing file')
    args = parser.parse_args()

    nlg = CyberNLG(lm_path='/roaming/tcastrof/gigaword/gigaword5.bin', beam=100)

    write_references(nlg.references, args.refs)
    write_hyps(nlg.hyps, args.hyps)