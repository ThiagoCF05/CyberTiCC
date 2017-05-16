__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 10/05/2017
Description:
    Prepare parallel corpus to Moses/GIZA:
    The source language is the sequence of triples, whereas the target is represented
    by the texts (delexicalised or not)
"""

import sys
sys.path.append('../')
from db.model import *

import utils

def get_parallel(set, delex=True, size=10):
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

        for lexEntry in entry.texts:
            if delex:
                target = lexEntry.template
            else:
                target = lexEntry.text


            # print source
            # print target
            # print 10 * '-'
            de.append(source.strip())
            en.append(target)
    return de, en

def write(fname, docs):
    f = open(fname, 'w')
    for doc in docs:
        f.write(doc)
        f.write('\n')
    f.close()

if __name__ == '__main__':
    DE_FILE = '../data/alignments/delex_train.de'
    EN_FILE = '../data/alignments/delex_train.en'
    de, en = get_parallel('train', True, 10)

    write(DE_FILE, de)
    write(EN_FILE, en)