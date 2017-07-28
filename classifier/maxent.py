__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 03/07/2017
Description:
    Maximum entropy classifier
"""

import sys
sys.path.append('../')
import cPickle as p
import copy
import json
import numpy as np

from nltk.classify import MaxentClassifier, accuracy
# import nltk

class CLFTraining(object):
    def __init__(self, ftrain, fdev, ftest):
        self.train = json.load(open(ftrain))
        self.dev = json.load(open(fdev))
        # self.test = json.load(open(ftest))

        step1_train_features, step2_train_features = self.extract_features(self.train)
        step1_dev_features, step2_dev_features = self.extract_features(self.dev)
        # step1_test_features, step2_test_features = self.extract_features(self.test)

        p.dump(step1_train_features, open('data/step1_train_features.cPickle', 'w'))
        p.dump(step2_train_features, open('data/step2_train_features.cPickle', 'w'))

        p.dump(step1_dev_features, open('data/step1_dev_features.cPickle', 'w'))
        p.dump(step2_dev_features, open('data/step2_dev_features.cPickle', 'w'))

        clf_step1 = MaxentClassifier.train(step1_train_features, 'megam', trace=0, max_iter=1000)
        # clf = nltk.NaiveBayesClassifier.train(trainset)
        p.dump(clf_step1, open('data/clf_step1.cPickle', 'w'))
        print 'Accuracy: ', accuracy(clf_step1, step1_dev_features)

        clf_step2 = MaxentClassifier.train(step2_train_features, 'megam', trace=0, max_iter=1000)
        # clf = nltk.NaiveBayesClassifier.train(trainset)
        p.dump(clf_step2, open('data/clf_step2.cPickle', 'w'))
        print 'Accuracy: ', accuracy(clf_step2, step2_dev_features)

    def step1_bayes(self, observations):
        '''
        :param observations: train_order.json file
        :return: probabilities of the first triple in the ordered array
        '''
        self.priori, self.posteriori = {}, {}
        posteriori_dem = {}

        smooth_priori = []
        smooth_posteriori = len(set(map(lambda obs: obs['semcategory'], observations)))

        for obs in observations:
            striples = map(lambda triple: tuple(triple.split(' | ')), obs['sorted'])

            smooth_priori.extend(map(lambda triple: triple[1], striples))

            if len(striples) > 1:
                first_pred = striples[0][1]
                if first_pred not in self.priori:
                    self.priori[first_pred] = 1
                else:
                    self.priori[first_pred] += 1

                semcat = obs['semcategory']
                if semcat not in posteriori_dem:
                    posteriori_dem[semcat] = 1
                else:
                    posteriori_dem[semcat] += 1

                if (first_pred, semcat) not in self.posteriori:
                    self.posteriori[(semcat, first_pred)] = 1
                else:
                    self.posteriori[(semcat, first_pred)] += 1

        smooth_priori = len(set(smooth_priori))
        priori_dem = sum(self.priori.values())
        for predicate in self.priori:
            self.priori[predicate] = (float(self.priori[predicate])+1) / (priori_dem+smooth_priori)

        for key in self.posteriori:
            semcat, predicate = key
            self.posteriori[key] = float(self.posteriori[key]+1) / (posteriori_dem[semcat]+smooth_posteriori)

        return {
            'priori':self.priori,
            'posteriori':self.posteriori,
            'smooth_priori':smooth_priori,
            'smooth_posteriori':smooth_posteriori,
            'priori_dem':priori_dem,
            'posteriori_dem':posteriori_dem
        }

    def step1(self, observations):
        self.features_1 = []

        for obs in observations:
            striples = map(lambda triple: tuple(triple.split(' | ')), obs['sorted'])

            if len(striples) > 1:
                for i, triple in enumerate(striples):
                    features = {}
                    features['predicate'] = triple[1]
                    features['semcategory'] = obs['semcategory']

                    if i == 0:
                        self.features_1.append((features, '1'))
                    else:
                        self.features_1.append((features, '0'))
        return self.features_1

    def step2(self, observations):
        self.features = []

        for obs in observations:
            striples = map(lambda triple: tuple(triple.split(' | ')), obs['sorted'])

            if len(striples) > 1:
                for i, triple1 in enumerate(striples):
                    for j in range(i+1, len(striples)):
                        triple2 = striples[j]

                        features = {}
                        features['predicate1'] = triple1[1]
                        features['predicate2'] = triple2[1]
                        features['semcategory'] = obs['semcategory']

                        if triple1[0] == triple2[0]:
                            features['same_agent'] = True
                        else:
                            features['same_agent'] = False

                        # if triple1[2] == triple2[2]:
                        #     features['same_patient'] = True
                        # else:
                        #     features['same_patient'] = False

                        # if triple1[0] == triple2[2] or triple1[2] == triple2[0]:
                        #     features['bridge'] = True
                        # else:
                        #     features['bridge'] = False

                        label = '0-1'
                        self.features.append((features, label))
                        ############################
                        # inverse
                        features = {}
                        features['predicate1'] = triple2[1]
                        features['predicate2'] = triple1[1]
                        features['semcategory'] = obs['semcategory']

                        if triple1[0] == triple2[0]:
                            features['same_agent'] = True
                        else:
                            features['same_agent'] = False

                        # if triple1[2] == triple2[2]:
                        #     features['same_patient'] = True
                        # else:
                        #     features['same_patient'] = False

                        # if triple1[0] == triple2[2] or triple1[2] == triple2[0]:
                        #     features['bridge'] = True
                        # else:
                        #     features['bridge'] = False

                        label = '1-0'
                        self.features.append((features, label))

        return self.features

    def extract_features(self, observations):
        self.priori, self.posteriori = {}, {}
        self.features = []

        step1 = self.step1(observations)

        step2 = self.step2(observations)

        return step1, step2

class CLF(object):
    def __init__(self, clf_step1, clf_step2):
        self.clf_step1 = p.load(open(clf_step1))
        self.clf_step2 = p.load(open(clf_step2))

    def _step1_features(self, triple, semcategory):
        features = {}
        features['predicate'] = triple.predicate.name
        features['semcategory'] = semcategory
        return features

    def _step2_features(self, triple1, triple2, semcategory):
        features = {}
        features['predicate1'] = triple1.predicate.name
        features['predicate2'] = triple2.predicate.name
        features['semcategory'] = semcategory

        if triple1.agent.name == triple2.agent.name:
            features['same_agent'] = True
        else:
            features['same_agent'] = False

        return features

    def step1_bayes(self, triples, semcategory, beam=2):
        '''
        :param triples:
        :param semcategory:
        :param beam:
        :return: candidates triples to the first position of ordered array
        '''

        priori, posteriori, smooth_pri, smooth_post, dem_pri, dem_post = self.clf_step1['priori'], \
                                                                         self.clf_step1['posteriori'], \
                                                                         self.clf_step1['smooth_priori'], \
                                                                         self.clf_step1['smooth_posteriori'], \
                                                                         self.clf_step1['priori_dem'], \
                                                                         self.clf_step1['posteriori_dem']
        ranking = []
        for triple in triples:
            predicate = triple.predicate.name
            if predicate in priori:
                p = float(priori[predicate]+1) / (dem_pri+smooth_pri)
            else:
                p = 1.0 / (dem_pri+smooth_pri)

            if (semcategory, predicate) in posteriori:
                post = float(posteriori[semcategory, predicate]+1) / (dem_post[semcategory]+smooth_post)
            else:
                post = 1.0 / (dem_post[semcategory]+smooth_post)

            prob = np.log(p * post)
            ranking.append(([triple], prob))

        candidates = sorted(ranking, key=lambda x: x[1], reverse=True)[:beam]
        return candidates

    def step1(self, triples, semcategory):
        ranking = []
        for triple in triples:
            features = self._step1_features(triple, semcategory)

            prob = self.clf_step1.prob_classify(features)
            ranking.append(([triple], prob._prob_dict['1']))

        ranking = sorted(ranking, key=lambda x: x[1], reverse=True)
        return ranking

    def step2(self, prev_triples, triples, semcategory):
        '''
        :param prev_triples:
        :param triples:
        :param semcategory:
        :return: sorted triples according to a maximum entropy classifier
        '''
        new_candidates = []

        triple1 = prev_triples[0][-1]
        ranking = []
        for triple2 in triples:
            features = self._step2_features(triple1, triple2, semcategory)

            prob = self.clf_step2.prob_classify(features)
            ranking.append((triple2, prob._prob_dict['0-1']))

        ranking = sorted(ranking, key=lambda x: x[1], reverse=True)
        for candidate in ranking:
            new_candidate = copy.deepcopy(prev_triples)
            new_candidate[0].append(candidate[0])
            new_candidate = (new_candidate[0], new_candidate[1] + candidate[1])

            new_candidates.append(new_candidate)

        return new_candidates

    def order(self, triples, semcategory, beam=2):
        candidates = self.step1(triples, semcategory)[:beam]

        for i in range(len(triples)-1):
            new_candidates = []
            for candidate in candidates:
                ftriples = filter(lambda triple: triple not in candidate[0], triples)
                result = self.step2(candidate, ftriples, semcategory)
                new_candidates.extend(result)

            new_candidates = sorted(new_candidates, key=lambda x: x[1], reverse=True)
            candidates = new_candidates[:beam]

        return candidates

if __name__ == '__main__':
    ftrain = 'data/train_order.json'
    fdev = 'data/dev_order.json'
    training = CLFTraining(ftrain, fdev, '')

    # entries = Entry.objects(set='dev', size=3)
    # entry = entries.first()
    #
    # clf = CLF('data/train_step1.cPickle', 'data/classifier.cPickle')
    # clf.order(entry.triples)