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
        self.pronoun_list = p.load(open('reg/pronoun_data/pronouns.cPickle'))

    def generate_major(self, prev_references, reference, data):
        entity = reference['entity']
        syntax = reference['syntax']

        pronouns = data[entity]
        if len(pronouns) == 0:
            if syntax == 'subj-det':
                pronoun = 'its'
            else:
                pronoun = 'it'
        else:
            pronoun = pronouns[0]

            if pronoun == 'he':
                if syntax == 'np-obj':
                    pronoun = 'him'
                elif syntax == 'subj-det':
                    pronoun = 'his'
            elif pronoun == 'she':
                if syntax != 'np-subj':
                    pronoun = 'her'
            elif pronoun == 'it':
                if syntax == 'subj-det':
                    pronoun = 'its'
                else:
                    pronoun = 'it'
            elif pronoun == 'they':
                if syntax == 'np-obj':
                    pronoun = 'them'
                elif syntax == 'subj-det':
                    pronoun = 'their'

        # Check for a competitor
        competitors = {
            'he':'he', 'his':'he',
            'she':'she', 'her':'she', 'hers':'she',
            'it':'it', 'its':'it',
            'we':'we', 'our':'we', 'ours':'we', 'us':'we',
            'they':'they', 'their':'they', 'theirs':'they', 'them':'they'
        }
        isCompetitor = False
        for prev_reference in prev_references:
            if prev_reference['entity'].name != entity and prev_reference['realization'].lower() in competitors:
                if competitors[prev_reference['realization'].lower()] == competitors[pronoun]:
                    isCompetitor = True
                    break

        return isCompetitor, pronoun

    def generate(self, prev_references, reference):
        '''
        :param prev_references: previous realized references
        :param reference: reference to be pronominalized
        :return: competitor flag (another entity realized with the same pronoun) and the proper pronoun for the context
        '''
        entity = reference['entity']
        syntax = reference['syntax']

        if (entity, syntax) in self.pronoun_list:
            pronoun = self.pronoun_list[(entity, syntax)][0][0].lower()
        else:
            if syntax == 'subj-det':
                pronoun = 'its'
            else:
                pronoun = 'it'

        # Check for a competitor
        competitors = {
            'he':'he', 'his':'he',
            'she':'she', 'her':'she', 'hers':'she',
            'it':'it', 'its':'it',
            'we':'we', 'our':'we', 'ours':'we', 'us':'we',
            'they':'they', 'their':'they', 'theirs':'they', 'them':'they'
        }
        isCompetitor = False
        for prev_reference in prev_references:
            if prev_reference['entity'].name != entity.name and prev_reference['realization'].lower() in competitors:
                if competitors[prev_reference['realization'].lower()] == competitors[pronoun]:
                    isCompetitor = True
                    break

        return isCompetitor, pronoun

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

    p.dump(pronouns, open('pronoun_data/pronouns.cPickle', 'w'))

if __name__ == '__main__':
    run()