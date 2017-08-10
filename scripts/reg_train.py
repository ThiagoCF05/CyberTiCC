__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 08/08/2017
Description:
    Compute frequency of referring expressions for each reference condition
"""

import sys
sys.path.append('../')
from db.model import *

import nltk

references = {}

refs = Reference.objects()

entities = Entity.objects()

for entity in entities:
    for syntax in ['np-subj', 'np-obj', 'subj-det']:
        for text_status in ['new', 'given']:
            for sentence_status in ['new', 'given']:
                reference = Reference.objects(entity=entity, syntax=syntax, text_status=text_status, sentence_status=sentence_status)

                if reference.count() > 0:
                    reference = reference.first()

                    references[(syntax, text_status, sentence_status, entity)] = {
                        'pronoun':[],
                        'description':[],
                        'demonstrative':[],
                        'name':[]
                    }

                    for refex in reference.refexes:
                        reftype = refex.ref_type
                        references[(syntax, text_status, sentence_status, entity)][reftype].append(refex.refex.strip())

for ref in refs:
    syntax = ref.syntax
    text_status = ref.text_status
    sentence_status = ref.sentence_status
    entity = ref.entity.name

    print syntax, text_status, sentence_status, entity
    references[(syntax, text_status, sentence_status, entity)] = {
        'pronoun':[],
        'description':[],
        'demonstrative':[],
        'name':[]
    }

    for refex in ref.refexes:
        reftype = refex.ref_type
        references[(syntax, text_status, sentence_status, entity)][reftype].append(refex.refex.strip())

    references[(syntax, text_status, sentence_status, entity)]['name'] = nltk.FreqDist(references[(syntax, text_status, sentence_status, entity)]['name'])
    references[(syntax, text_status, sentence_status, entity)]['pronoun'] = nltk.FreqDist(references[(syntax, text_status, sentence_status, entity)]['pronoun'])
    references[(syntax, text_status, sentence_status, entity)]['description'] = nltk.FreqDist(references[(syntax, text_status, sentence_status, entity)]['description'])
    references[(syntax, text_status, sentence_status, entity)]['demonstrative'] = nltk.FreqDist(references[(syntax, text_status, sentence_status, entity)]['demonstrative'])

f = open('reg', 'w')
for key in references:
    f.write('\t'.join(list(key)).encode('utf-8'))
    f.write('\n')

    refexes = sorted(references[key]['name'].items(), key=lambda x: x[1], reverse=True)[:2]
    for refex in refexes:
        f.write('\t'.join(['name', refex[0], str(refex[1])]).encode('utf-8'))
        f.write('\n')

    refexes = sorted(references[key]['pronoun'].items(), key=lambda x: x[1], reverse=True)[:2]
    for refex in refexes:
        f.write('\t'.join(['pronoun', refex[0], str(refex[1])]).encode('utf-8'))
        f.write('\n')

    refexes = sorted(references[key]['description'].items(), key=lambda x: x[1], reverse=True)[:2]
    for refex in refexes:
        f.write('\t'.join(['description', refex[0], str(refex[1])]).encode('utf-8'))
        f.write('\n')

    refexes = sorted(references[key]['demonstrative'].items(), key=lambda x: x[1], reverse=True)[:2]
    for refex in refexes:
        f.write('\t'.join(['demonstrative', refex[0], str(refex[1])]).encode('utf-8'))
        f.write('\n')
    f.write(10 * '-')
    f.write('\n')
f.close()