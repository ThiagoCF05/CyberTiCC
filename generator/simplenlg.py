__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 18/05/2017
Description:
    Simple natural language generation system which retrieves text templates
    based on the order of the predicates
"""

import argparse
import sys
sys.path.append('../')
from db.model import *
import nltk
import operator
import utils

from reg.reg_main import REG

class EasyNLG(object):
    def __init__(self):
        self.references = []
        self.hyps = []

        self.reg = REG()

        deventries = Entry.objects(set='dev').timeout(False)
        for deventry in deventries:
            self.process(deventry)

    def extract_template(self, triples):
        # entity and predicate mapping
        entitymap, predicates = utils.map_entities(triples=triples)

        trainentries = Entry.objects(size=len(triples), set='train')
        for i, triple in enumerate(triples):
            trainentries = filter(lambda entry: entry.triples[i].predicate.name == triple.predicate.name, trainentries)

        # extract templates
        templates = []
        for entry in trainentries:
            for lexEntry in entry.texts:
                template = lexEntry.template

                entitiesPresence = True
                for tag in entitymap:
                    if tag not in template:
                        entitiesPresence = False
                        break
                if entitiesPresence:
                    templates.append(template)

        templates = nltk.FreqDist(templates)
        item = sorted(templates.items(), key=operator.itemgetter(1), reverse=True)
        if len(item) == 0:
            template, freq = '', 0
        else:
            template, freq = item[0]
            # REPLACE ENTITY TAGS FOR WIKIPEDIA IDs
            for tag, entity in sorted(entitymap.items(), key=lambda x: len(x[1].name), reverse=True):
                template = template.replace(tag, '_'.join(entity.name.replace('\'', '').replace('\"', '').split()))
        return template, entitymap, predicates

    def get_new_entitymap(self, entitymap):
        new_entitymap = {}

        tags = sorted(entitymap.keys())
        for i, tag in enumerate(tags):
            new_tag = 'ENTITY-' + str(i+1)
            new_entitymap[entitymap[tag]] = new_tag
        return new_entitymap

    def process(self, deventry):
        # extract references
        refs = []
        for lexEntry in deventry.texts:
            text = lexEntry.text
            refs.append(text)
        self.references.append(refs)

        # Try to extract a full template
        template, entitymap, predicates = self.extract_template(deventry.triples)

        # In case the template is not found, the search is splitted in two
        if template.strip() == '':
            template1, template2 = '', ''
            i = len(deventry.triples)

            # while one of the two the templates is empty...
            history = []
            while (template1 == '' or template2 == '') and i > 0:
                triple1, triple2 = deventry.triples[:i], deventry.triples[i:]

                template1, _, _ = self.extract_template(triple1)
                template2, _, _ = self.extract_template(triple2)

                history.append({'triple1':triple1, 'triple2':triple2, 'template1':template1, 'template2':template2})
                i = i - 1

            # If two templates are found, return them. Otherwise, get the longest template and realize others separately
            if template1 != '' and template2 != '':
                template = template1 + ' ' + template2
                template = template.strip()
            else:
                best_aggregation = {}
                for h in history:
                    if h['template1'] != '':
                        if 'maxtriple' not in best_aggregation:
                            best_aggregation['maxtriple'] = h['triple1']
                            best_aggregation['template'] = h['template1']
                            best_aggregation['remaining'] = h['triple2']
                        elif len(best_aggregation['maxtriple']) < len(h['triple1']):
                            best_aggregation['maxtriple'] = h['triple1']
                            best_aggregation['template'] = h['template1']
                            best_aggregation['remaining'] = h['triple2']
                    else:
                        if 'maxtriple' not in best_aggregation:
                            best_aggregation['maxtriple'] = h['triple2']
                            best_aggregation['template'] = h['template2']
                            best_aggregation['remaining'] = h['triple1']
                        elif len(best_aggregation['maxtriple']) < len(h['triple2']):
                            best_aggregation['maxtriple'] = h['triple2']
                            best_aggregation['template'] = h['template2']
                            best_aggregation['remaining'] = h['triple1']

                template = best_aggregation['template']
                for triple in best_aggregation['remaining']:
                    template = template + ' ' + self.extract_template([triple])[0]

        # Replace WIKI-IDS for simple tags (ENTITY-1, etc). In order to make it easier for the parser
        new_entitymap = self.get_new_entitymap(entitymap)
        for entity, tag in sorted(new_entitymap.items(), key=lambda x: len(x[0].name), reverse=True):
            name = '_'.join(entity.name.replace('\'', '').replace('\"', '').split())
            template = template.replace(name, tag)

        # Generating referring expressions
        new_entitymap = dict(map(lambda x: (x[1], x[0]), new_entitymap.items()))
        template = self.reg.generate(template, new_entitymap)

        self.hyps.append(template.strip())

        print 10 * '-'
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

    nlg = EasyNLG()

    write_references(nlg.references, args.refs)
    write_hyps(nlg.hyps, args.hyps)