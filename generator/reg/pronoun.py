__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 07/06/2017
Description:
    This script aims to extract all pronoun per entity in each syntactic position
"""
import sys
sys.path.append('../../')
import cPickle as p
import nltk

from db.model import *

class Pronominalization(object):
    def __init__(self):
        self.pronoun_list = p.load(open('reg/pronouns.cPickle'))

    def generate(self, reference):
        entity = reference['entity']
        syntax = reference['syntax']

        if (entity, syntax) in self.pronoun_list:
            return self.pronoun_list[(entity, syntax)][0][0].lower()
        else:
            if syntax == 'subj-det':
                return 'its'
            else:
                return 'it'

def run():
    references = Reference.objects()

    pronouns = {}
    for ref in references:
        entity = ref.entity.name
        syntax = ref.syntax

        for refex in ref.refexes:
            if refex.ref_type == 'pronoun':
                if (entity, syntax) not in pronouns:
                    pronouns[(entity, syntax)] = []
                pronouns[(entity, syntax)].append(refex.refex.lower())

    for k in pronouns:
        pronouns[k] = nltk.FreqDist(pronouns[k])
        pronouns[k] = sorted(pronouns[k].items(), key=lambda x: x[1], reverse=True)[:2]

    p.dump(pronouns, open('pronouns.cPickle', 'w'))

if __name__ == '__main__':
    run()