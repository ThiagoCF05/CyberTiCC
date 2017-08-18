__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 10/05/2017
Description:
    Prepare parallel corpus to Moses/GIZA:
    The source language is the sequence of triples, whereas the target is represented
    by the texts (delexicalised or not)
    Referring expressions are also included in the files
"""

import argparse
import cPickle as p
import sys
sys.path.append('../')
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')

from db.model import *
from stanford_corenlp_pywrapper import CoreNLP

import utils

def get_references():
    de, en = [], []
    proc = CoreNLP('ssplit')

    references = Reference.objects()
    for ref in references:
        _de = ref.entity.name

        for refex in ref.refexes:
            if refex.annotation == 'manual':
                _en = refex.refex
                de.append(_de)
                en.append(_en)

    # Insert test references in training data
    entries = Entry.objects(set='test')
    for entry in entries:
        for triple in entry.triples:
            agent = triple.agent.name
            patient = triple.patient.name

            de.append(agent)
            name = ' '.join(agent.replace('\'', '').replace('\"', '').split('_'))
            out = proc.parse_doc(name)
            text = ''
            for snt in out['sentences']:
                text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
                text += ' '
            en.append(text.strip())

            de.append(patient)
            name = ' '.join(patient.replace('\'', '').replace('\"', '').split('_'))
            out = proc.parse_doc(name)
            text = ''
            for snt in out['sentences']:
                text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
                text += ' '
            en.append(text.strip())
    return de, en

def get_parallel(set, delex=True, size=10, evaluation=False):
    entries = Entry.objects(size__lte=size, set=set)
    proc = CoreNLP('ssplit')

    de, en, entity_maps = [], [], []
    for entry in entries:
        entity_map, predicates = utils.map_entities(entry.triples)
        entity2tag = utils.entity2tag(entity_map)

        source = ''
        for triple in entry.triples:
            agent = triple.agent.name
            tag_agent = entity2tag[agent]

            predicate = triple.predicate.name

            patient = triple.patient.name
            tag_patient = entity2tag[patient]

            if delex:
                source += tag_agent
            else:
                source += agent
            source += ' '
            source += predicate
            source += ' '
            if delex:
                source += tag_patient
            else:
                source += patient
            source += ' '

            de.append(agent)
            name = ' '.join(agent.replace('\'', '').replace('\"', '').split('_'))
            out = proc.parse_doc(name)
            text = ''
            for snt in out['sentences']:
                text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
                text += ' '
            en.append(text.strip())

            de.append(patient)
            name = ' '.join(patient.replace('\'', '').replace('\"', '').split('_'))
            out = proc.parse_doc(name)
            text = ''
            for snt in out['sentences']:
                text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
                text += ' '
            en.append(text.strip())

        target_list = []
        for lexEntry in entry.texts:
            if delex and not evaluation:
                target = lexEntry.template
            else:
                target = lexEntry.text
            out = proc.parse_doc(target)

            text = ''
            for snt in out['sentences']:
                text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
                text += ' '
            target = text.strip()
            target_list.append(target)

            print source
            print target
            print 10 * '-'
            if not evaluation:
                entity_maps.append(entity_map)
                de.append(source.strip())
                en.append(target)
        if evaluation:
            entity_maps.append(entity_map)
            de.append(source.strip())
            en.append(target_list)
        elif set == 'test':
            entity_maps.append(entity_map)
            de.append(source.strip())
    return de, en, entity_maps

def write(fname, docs):
    f = open(fname, 'w')
    for doc in docs:
        f.write(doc.lower().encode('utf-8'))
        f.write('\n')
    f.close()

if __name__ == '__main__':
    # python parallel_data.py /home/tcastrof/cyber/data/delex/train.de /home/tcastrof/cyber/data/delex/train.en 10 --dev --delex --eval

    parser = argparse.ArgumentParser()
    parser.add_argument('f', type=str, default='/home/tcastrof/cyber/data/delex/train', help='language file')
    parser.add_argument('size', type=int, default=10, help='consider sentences with less or equal to N triples')
    parser.add_argument("--dev", action="store_true", help="development set")
    parser.add_argument("--test", action="store_true", help="test set")
    parser.add_argument("--delex", action="store_true", help="delexicalized templates")
    parser.add_argument("--references", action="store_true", help="include references")
    parser.add_argument("--eval", action="store_true", help="evaluation mode")

    args = parser.parse_args()

    FILE = args.f
    SIZE = args.size
    SET = 'train'
    if args.test:
        SET = 'test'
    if args.dev:
        SET = 'dev'
    DELEX = args.delex
    EVAL =  args.eval
    REFS = args.references

    de, en, entity_maps = get_parallel(SET, DELEX, SIZE, EVAL)
    # insert references only in the training set
    if not EVAL and SET == 'train' and REFS:
        ref_de, ref_en = get_references()

        de.extend(ref_de)
        en.extend(ref_en)

    write(FILE+'.de', de)
    if EVAL:
        utils.write_references(FILE+'.en', en)
    else:
        write(FILE+'.en', en)

    p.dump(entity_maps, open(FILE+'.cPickle', 'w'))