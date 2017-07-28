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
import sys
sys.path.append('../')
from db.model import *

import utils

def get_references():
    de, en = [], []

    references = Reference.objects()
    for ref in references:
        _de = ref.entity.name

        for refex in ref.refexes:
            _en = refex.refex
            de.append(_de)
            en.append(_en)
    return de, en

def get_parallel(set, delex=True, size=10, evaluation=False):
    entries = Entry.objects(size__lte=size, set=set)

    de, en = [], []
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

        target_list = []
        for lexEntry in entry.texts:
            if delex:
                target = lexEntry.template
            else:
                target = lexEntry.text
            target_list.append(target)


            print source
            print target
            print 10 * '-'
            if not evaluation:
                de.append(source.strip())
                en.append(target)
        if evaluation:
            de.append(source.strip())
            en.append(target_list)
    return de, en

def write(fname, docs):
    f = open(fname, 'w')
    for doc in docs:
        f.write(doc.encode('utf-8'))
        f.write('\n')
    f.close()

if __name__ == '__main__':
    # python parallel_data.py /home/tcastrof/cyber/data/delex/train.de /home/tcastrof/cyber/data/delex/train.en 10 --dev --delex --eval

    parser = argparse.ArgumentParser()
    parser.add_argument('de', type=str, default='/home/tcastrof/cyber/data/delex/train.de', help='source language file')
    parser.add_argument('en', type=str, default='/home/tcastrof/cyber/data/delex/train.en', help='target language file')
    parser.add_argument('size', type=int, default=10, help='consider sentences with less or equal to N triples')
    parser.add_argument("--dev", action="store_true", help="development set")
    parser.add_argument("--delex", action="store_true", help="delexicalized templates")
    parser.add_argument("--eval", action="store_true", help="evaluation mode")

    args = parser.parse_args()

    DE_FILE = args.de
    EN_FILE = args.en
    SIZE = args.size
    SET = 'train'
    if args.dev:
        SET = 'dev'
    DELEX = args.delex
    EVAL =  args.eval

    de, en = get_parallel(SET, DELEX, SIZE, EVAL)
    if not EVAL:
        ref_de, ref_en = get_references()

        de.extend(ref_de)
        en.extend(ref_en)

    write(DE_FILE, de)
    if EVAL:
        utils.write_references(EN_FILE, en)
    else:
        write(EN_FILE, en)