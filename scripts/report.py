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
import utils

entries = Entry.objects(set='train')

f = open('report.txt', 'w')
for entry in entries:
    f.write('\n')
    f.write('Entry: ' + str(entry.docid))
    f.write('\n\nTRIPLES\n')
    for triple in entry.triples:
        str_triple = triple.agent.name + ' | ' + triple.predicate.name + ' | ' + triple.patient.name
        f.write(str_triple.encode('utf-8') + '\n')

    f.write('\n\nENTITY MAP\n')
    entitymap, predicates = utils.map_entities(entry.triples)
    for tag, entity in entitymap.iteritems():
        f.write(tag.encode('utf-8') + ' | ' + entity.encode('utf-8') + '\n')

    f.write('\n\nLEX\n')
    for lex in entry.texts:
        f.write(lex.text.encode('utf-8') + '\n')
        f.write(lex.template.encode('utf-8') + '\n')
        f.write('-\n')
    f.write('\n')
    f.write(50 * '*')
    f.write('\n')
