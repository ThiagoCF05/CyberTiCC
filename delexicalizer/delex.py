__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 03/05/2017
Description:
    Delexicalizing entities from the text based on the triples
"""

import sys
sys.path.append('../')
from db.model import *

if __name__ == '__main__':
    entries = Entry.objects(size=1, set='train')

    for entry in entries:
        triple = entry.triples[0]

        agent = triple.agent.name
        predicate = triple.predicate.name
        patient = triple.patient.name

        print 10 * '-'
        print agent, predicate, patient

        lexEntries = entry.texts
        for lexEntry in lexEntries:
            print lexEntry.text
        print 10 * '-'