__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 13/06/2017
Description:
    Generates a report, showing texts and their templates after delexicalization
"""

import sys
sys.path.append('../')
from db.model import *

entries = Entry.objects(set='train')

f = open('report.txt')
for entry in entries:
    f.write('\n')
    f.write('Entry: ' + str(entry.docid))
    f.write('\n\nTRIPLES\n')
    for triple in entry.triples:
        str_triple = triple.agent.name + ' | ' + triple.predicate.name + ' | ' + triple.patient.name
        f.write(str_triple + '\n')

    f.write('\n\nLEX\n')
    for lex in entry.texts:
        f.write(lex.text + '\n')
        f.write(lex.template + '\n')
    f.write('\n')
    f.write(50 * '*' + '\n')
