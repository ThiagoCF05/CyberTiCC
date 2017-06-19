__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 19/06/2017
Description:
    Populate database with entity information like NER tag, semantic category and description
"""

import sys
sys.path.append('../')
from db.model import *

import db.operations as dbop
import json

ner = json.load(open('../data/delexicalization/ner_dict.json'))
semcategory = json.load(open('../data/delexicalization/delex_dict.json'))
descriptions = json.load(open('../data/delexicalization/descriptions.json'))

entities = Entity.objects(type='wiki')

def get_ner(entity):
    return filter(lambda key: entity.name in ner[key], ner)

def get_category(entity):
    return filter(lambda key: entity.name in semcategory[key], semcategory)

missing, total = 0, 0
missinginst = []
for entity in entities:
    ner_tag = get_ner(entity)
    if len(ner_tag) > 0:
        dbop.add_ner(entity, ner_tag[0])
    else:
        missing += 1
        missinginst.append(entity.name)

    total += 1

    category = get_category(entity)
    if len(category) > 0:
        dbop.add_ner(entity, category[0])

print str(missing), str(total)

for row in sorted(missinginst):
    print row