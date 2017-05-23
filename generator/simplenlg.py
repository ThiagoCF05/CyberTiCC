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

def write_references(refs, fname):
    f1 = open(fname+'1', 'w')
    f2 = open(fname+'2', 'w')
    f3 = open(fname+'3', 'w')
    f4 = open(fname+'4', 'w')
    f5 = open(fname+'5', 'w')

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

    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()

def write_hyps(hyps, fname):
    f = open(fname, 'w')
    for hyp in hyps:
        f.write(hyp.encode('utf-8'))
        f.write('\n')
    f.close()

def main():
    deventries = Entry.objects(set='dev')

    references, hyps = [], []

    for deventry in deventries:
        # entity and predicate mapping
        entitymap, predicates = utils.map_entities(triples=deventry.triples)

        trainentries = Entry.objects(size=len(deventry.triples), set='train')
        for i, triple in enumerate(deventry.triples):
            trainentries = filter(lambda entry: entry.triples[i].predicate.name == triple.predicate.name, trainentries)

        # extract references
        refs = []
        for lexEntry in deventry.texts:
            text = lexEntry.text
            refs.append(text)
        references.append(refs)

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
            for tag, name in entitymap.iteritems():
                template = template.replace(tag, ' '.join(name.split('_')))

        print 10 * '-'
        print 'Entities: ', str(entitymap)
        print 'Predicate: ', str(predicates)
        print template.encode('utf-8'), freq
        print 10 * '-'

        hyps.append(template)
    return hyps, references

if __name__ == '__main__':
    # python simplenlg.py /home/tcastrof/cyber/data/easy_nlg/hyps /home/tcastrof/cyber/data/easy_nlg/ref
    parser = argparse.ArgumentParser()
    parser.add_argument('hyps', type=str, default='/home/tcastrof/cyber/data/easy_nlg/hyps', help='hypothesis writing file')
    parser.add_argument('refs', type=str, default='/home/tcastrof/cyber/data/easy_nlg/ref', help='references writing file')
    args = parser.parse_args()

    hyps, references = main()

    write_references(references, args.refs)
    write_hyps(hyps, args.hyps)