__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 02/06/2017
Description:
    Proper name generation
"""

import sys
sys.path.append('../../')
from db.model import *
import nltk
import operator

class ProperNameTraining(object):
    def __init__(self):
        references = Reference.objects()

        self.trainset = {}
        self.trainset_backoff = {}
        for reference in references:
            text_status = reference.text_status
            entity = reference.entity.name

            for refex in reference.refexes:
                if refex.ref_type == u'name':
                    tokens = [u'<S>'] + nltk.word_tokenize(refex.refex) + [u'</S>']

                    bigrams = nltk.bigrams(tokens)
                    for bigram in bigrams:
                        if (text_status, entity, bigram[0]) not in self.trainset:
                            self.trainset[(text_status, entity)] = []
                        if entity not in self.trainset_backoff:
                            self.trainset_backoff[entity] = []

                        self.trainset[(text_status, entity, bigram[0])].append(bigram[1])
                        self.trainset_backoff[(entity, bigram[0])].append(bigram[1])

        keys = sorted(self.trainset.keys(), key=lambda x: (x[0], x[1], x[2]))
        for key in keys:
            entity, text_status, n_tm1 = key

            self.trainset[key] = nltk.FreqDist(self.trainset[key])
            self.trainset[key] = sorted(self.trainset[key].items(), key=operator.itemgetter(1), reverse=True)[:3]

            self.trainset_backoff[(entity, n_tm1)] = nltk.FreqDist(self.trainset_backoff[(entity, n_tm1)])
            self.trainset_backoff[(entity, n_tm1)] = sorted(self.trainset_backoff[(entity, n_tm1)].items(), key=operator.itemgetter(1), reverse=True)[:3]

    def write(self):
        f = open('name_distribution.txt', 'w')
        for key in self.trainset:
            entity, text_status, n_tm1 = key
            f.write(entity.encode('utf-8'))
            f.write('\t')
            f.write(text_status.encode('utf-8'))
            f.write('\t')
            f.write(n_tm1.encode('utf-8'))
            f.write('\n')

            for word in self.trainset[key]:
                f.write(word[0].encode('utf-8'))
                f.write('\t')
                f.write(word[1].encode('utf-8'))
                f.write('\n')
            f.write('\n')
        f.close()

        f = open('name_backoff_distribution.txt', 'w')
        for key in self.trainset_backoff:
            entity, n_tm1 = key
            f.write(entity.encode('utf-8'))
            f.write('\t')
            f.write(n_tm1.encode('utf-8'))
            f.write('\n')

            for word in self.trainset[key]:
                f.write(word[0].encode('utf-8'))
                f.write('\t')
                f.write(word[1].encode('utf-8'))
                f.write('\n')
            f.write('\n')
        f.close()

if __name__ == '__main__':
    train = ProperNameTraining()
    train.write()