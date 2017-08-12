__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 22/06/2017
Description:
    Simple natural language generation system which retrieves text templates
    based on the order of the predicates
"""

import argparse
import copy
import sys
sys.path.append('../')
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from db.model import *
from mongoengine.queryset.visitor import Q
import kenlm
import nltk
import operator
import utils

from classifier.maxent import CLF
from reg.reg_main import REG
from stanford_corenlp_pywrapper import CoreNLP

class CyberNLG(object):
    def __init__(self, lm, clf, beam, clf_beam, delex_type):
        self.references = []
        self.hyps = []

        self.clf = clf
        self.clf_beam = clf_beam

        self.model = lm
        self.beam = beam

        self.delex_type = delex_type

        self.reg = REG('/home/tcastrof/cyber/CyberTiCC/generator/reg/data.cPickle')

        deventries = Entry.objects(set='dev').timeout(False)
        for deventry in deventries:
            self.run(deventry)

    def get_new_entitymap(self, entitymap):
        '''
        Get tag -> entity mapping with new tags (ENTITY-1, ENTITY-2, etc)
        :param entitymap:
        :return:
        '''
        new_entitymap = {}

        tags = sorted(entitymap.keys())
        for i, tag in enumerate(tags):
            new_tag = 'entity-' + str(i+1)
            new_entitymap[entitymap[tag]] = new_tag
        return new_entitymap

    def reg_process(self, templates, entitymap):
        '''
        Process for lexicalization of the templates (referring expression genenation)
        :param self:
        :param templates:
        :param entitymap:
        :return:
        '''
        new_templates = []
        for template in templates:
            # Replace WIKI-IDS for simple tags (ENTITY-1, etc). In order to make it easier for the parser
            new_entitymap = self.get_new_entitymap(entitymap)
            for entity, tag in sorted(new_entitymap.items(), key=lambda x: len(x[0].name), reverse=True):
                name = '_'.join(entity.name.replace('\'', '').replace('\"', '').split())
                template = template.replace(name, tag)

            # Generating referring expressions
            new_entitymap = dict(map(lambda x: (x[1], x[0]), new_entitymap.items()))
            template = self.reg.generate(template, new_entitymap)
            new_templates.append(template)
        return new_templates

    def order_process(self, triples, semcategory):
        '''
        Ordering method
        :param self:
        :param triples:
        :param semcategory:
        :return:
        '''
        striples = clf.order(triples, semcategory, self.clf_beam)
        return striples

    def _extract_template(self, triples, semcategory=''):
        '''
        Extract templates based on the triple set
        :param self:
        :param triples: triple set
        :return: templates, tag->entity map and predicates
        '''
        # entity and predicate mapping
        entitymap, predicates = utils.map_entities(triples=triples)

        # Select templates that have the same predicates (in the same order??) than the input triples
        if self.delex_type in ['automatic', 'manual']:
            if semcategory == '':
                train_templates = Template.objects(Q(triples__size=len(triples)) & Q(delex_type=self.delex_type))
            else:
                train_templates = Template.objects(Q(triples__size=len(triples)) & Q(delex_type=self.delex_type) & Q(category=semcategory))
        else:
            if semcategory == '':
                train_templates = Template.objects(triples__size=len(triples))
            else:
                train_templates = Template.objects(Q(triples__size=len(triples)) & Q(category=semcategory))

        for i, triple in enumerate(triples):
            train_templates = filter(lambda train_template: train_template.triples[i].predicate.name == triple.predicate.name, train_templates)

        # for i, triple in enumerate(triples):
        #     new_train_templates = []
        #     for train_template in train_templates:
        #         if triple.predicate.name in map(lambda triple: triple.predicate.name, train_template.triples):
        #             new_train_templates.append(train_template)
        #     train_templates = copy.deepcopy(new_train_templates)

        # extract templates
        templates = []
        for entry in train_templates:
            template = entry.template

            entitiesPresence = True
            for tag in entitymap:
                if tag not in template:
                    entitiesPresence = False
                    break
            if entitiesPresence:
                templates.append(template)

        templates = nltk.FreqDist(templates)
        templates = sorted(templates.items(), key=operator.itemgetter(1), reverse=True)

        new_templates = []
        dem = sum(map(lambda item: item[1], templates))
        for item in templates:
            template, freq = item
            # REPLACE ENTITY TAGS FOR WIKIPEDIA IDs
            for tag, entity in sorted(entitymap.items(), key=lambda x: len(x[1].name), reverse=True):
                template = template.replace(tag, '_'.join(entity.name.replace('\'', '').replace('\"', '').split()))
            new_templates.append((template, float(freq)/dem))

        if len(new_templates) == 0 and semcategory != '':
            new_templates, entitymap, predicates = self._extract_template(triples, '')

        return new_templates, entitymap, predicates

    def template_process(self, triples, semcategory=''):
        '''
        Process a set of triples, extracting the sentence templates that describe it
        :param self:
        :param triples:
        :return:
        '''
        # Try to extract a full template
        begin, end, templates = 0, len(triples), []
        while begin < len(triples):
            partial_templates, entitymap, predicates = self._extract_template(triples[begin:end], semcategory)[:self.beam]

            if len(partial_templates) > 0:
                if len(templates) == 0:
                    templates = map(lambda template: ([template[0]], template[1]), partial_templates)
                else:
                    new_templates = []
                    for i, template in enumerate(templates):
                        for partial_template in partial_templates:
                            new_template = (templates[i][0] + [partial_template[0]], templates[i][1] * partial_template[1])
                            new_templates.append(new_template)

                    templates = sorted(new_templates, key=lambda template: template[1], reverse=True)[:self.beam]

                begin = copy.copy(end)
                end = len(triples)
            else:
                end -= 1

                # jump a triple if it is not on training set
                if begin == end:
                    begin += 1
                    end = len(triples)
        return templates

    def run(self, deventry):
        print 10 * '-'
        print 'ID:', str(deventry.docid), str(deventry.size), str(deventry.category)

        # extract references (gold standard)
        refs = []
        for lexEntry in deventry.texts:
            text = lexEntry.text
            refs.append(text)
        self.references.append(refs)

        # ordering triples
        triples = deventry.triples
        semcategory = deventry.category
        striples = self.order_process(triples, semcategory)

        # Templates selection
        templates = []
        for triples in striples:
            templates.extend(self.template_process(triples[0], semcategory))

        templates = sorted(templates, key=lambda template: template[1], reverse=True)[:self.beam]

        # Referring expression generation
        entitymap, predicates = utils.map_entities(deventry.triples)
        templates = map(lambda template: ' '.join(template[0]), templates)
        templates = self.reg_process(templates, entitymap)

        # Ranking with KenLM
        # templates = sorted(templates, key=lambda x: self.model.score(x), reverse=True)
        if len(templates) > 0:
            template = templates[0]
        else:
            template = ''

        self.hyps.append(template.strip())

        print 'Entities: ', str(map(lambda x: (x[0], x[1].name), entitymap.items()))
        print 'Predicate: ', str(map(lambda predicate: predicate.name, predicates))
        print template.encode('utf-8')
        print 10 * '-'
        return template

def write_references(refs, fname):
    def get_tok_lw(reference, proc):
        ref = reference
        out = proc.parse_doc(ref)
        text = ''
        for snt in out['sentences']:
            text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
            text += ' '
        text = text.strip().lower()
        return text

    f1 = open(fname+'1', 'w')
    f2 = open(fname+'2', 'w')
    f3 = open(fname+'3', 'w')
    f4 = open(fname+'4', 'w')
    f5 = open(fname+'5', 'w')
    f6 = open(fname+'6', 'w')
    f7 = open(fname+'7', 'w')

    proc = CoreNLP('ssplit')

    for references in refs:
        text = get_tok_lw(references[0], proc)

        f1.write(text.encode('utf-8'))
        f1.write('\n')

        if len(references) >= 2:
            text = get_tok_lw(references[1], proc)
            f2.write(text.encode('utf-8'))
        f2.write('\n')

        if len(references) >= 3:
            text = get_tok_lw(references[2], proc)
            f3.write(text.encode('utf-8'))
        f3.write('\n')

        if len(references) >= 4:
            text = get_tok_lw(references[3], proc)
            f4.write(text.encode('utf-8'))
        f4.write('\n')

        if len(references) >= 5:
            text = get_tok_lw(references[4], proc)
            f5.write(text.encode('utf-8'))
        f5.write('\n')

        if len(references) >= 6:
            text = get_tok_lw(references[5], proc)
            f6.write(text.encode('utf-8'))
        f6.write('\n')

        if len(references) >= 7:
            text = get_tok_lw(references[6], proc)
            f7.write(text.encode('utf-8'))
        f7.write('\n')

    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()
    f6.close()
    f7.close()

def write_hyps(hyps, fname):
    f = open(fname, 'w')
    for hyp in hyps:
        f.write(hyp.encode('utf-8'))
        f.write('\n')
    f.close()

if __name__ == '__main__':
    # python simplenlg.py /home/tcastrof/cyber/data/easy_nlg/hyps /home/tcastrof/cyber/data/easy_nlg/ref
    parser = argparse.ArgumentParser()
    parser.add_argument('hyps', type=str, default='/home/tcastrof/cyber/data/easy_nlg/hyps', help='hypothesis writing file')
    parser.add_argument('refs', type=str, default='/home/tcastrof/cyber/data/easy_nlg/ref', help='references writing file')
    parser.add_argument('delex_type', type=str, default='automatic+manual', help='delexicalization type (manual or automatic)')
    args = parser.parse_args()

    # lm = kenlm.Model('/roaming/tcastrof/gigaword/gigaword.bin')
    lm = None

    order_step1, order_step2 = '../classifier/data/clf_step1.cPickle', '../classifier/data/clf_step2.cPickle'
    clf = CLF(clf_step1=order_step1, clf_step2=order_step2)

    nlg = CyberNLG(lm=lm, clf=clf, beam=100, clf_beam=3, delex_type=args.delex_type)

    write_references(nlg.references, args.refs)
    write_hyps(nlg.hyps, args.hyps)