__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 07/06/2017
Description:
    Main code for Referring expression generation
"""

import cPickle as p
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('../')
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP
from db.model import *

import pronoun as prp
import proper_name as nnp
import description as dsc
import form_choice
import re

class SimpleREG(object):
    def run(self, fin, fout):
        self.proc = CoreNLP('ssplit')

        entity_maps = p.load(open(os.path.join(fin, 'eval1.cPickle')))

        f = open(os.path.join(fin, 'eval1.bpe.de.output.postprocessed.dev'))
        texts = f.read().lower().split('\n')
        f.close()

        print len(texts), len(entity_maps)

        for i, text in enumerate(texts[:-1]):
            entity_map = entity_maps[i]
            for tag in entity_map:
                name = ' '.join(entity_map[tag].name.lower().replace('\'', '').replace('\"', '').split('_'))
                texts[i] = texts[i].replace(tag.lower(), str(name))

        f = open(fout, 'w')
        for text in texts:
            out = self.proc.parse_doc(text)['sentences']

            text = []
            for i, snt in enumerate(out):
                text.extend(snt['tokens'])
            text = ' '.join(text).replace('-LRB- ', '(').replace(' -RRB-', ')').strip()

            f.write(text.encode('utf-8'))
            f.write('\n')
        f.close()

class REG(object):
    def __init__(self, fdata):
        self.data = p.load(open(fdata))
        self.proc = CoreNLP('parse')
        self.nnp = nnp.ProperNameGeneration()
        self.prp = prp.Pronominalization()
        self.dsc = dsc.DescriptionGeneration()

    def _extract_references(self):
        out = self.proc.parse_doc(self.template)['sentences']

        references = []
        # Extract reference and classify their syntactic position based on a dependency tree
        for tag in self.entitymap:
            for i, snt in enumerate(out):
                deps = snt['deps_cc']
                visited_tokens = []
                for dep in deps:
                    if snt['tokens'][dep[2]] == tag and dep[2] not in visited_tokens:
                        visited_tokens.append(dep[2])
                        reference = {'syntax':'', 'sentence':i, 'pos':dep[2], 'tag':tag, 'entity':self.entitymap[tag], 'no_pronoun':False}
                        if 'nsubj' in dep[0] or 'nsubjpass' in dep[0]:
                            reference['syntax'] = 'np-subj'
                        elif 'nmod:poss' in dep[0]:
                            reference['syntax'] = 'subj-det'
                        elif 'iobj' in dep[0] or 'dobj' in dep[0] or 'nmod' in dep[0]:
                            reference['syntax'] = 'np-obj'
                        else:
                            if 'compound' in dep[0]:
                                reference['no_pronoun'] = True
                            reference['syntax'] = 'np-obj'
                        references.append(reference)

        # Classify the references by text and sentence status
        references = sorted(references, key=lambda x: (x['entity'].name, x['sentence'], x['pos']))
        sentence_statuses = {}
        for i, reference in enumerate(references):
            if i == 0 or (reference['entity'].name != references[i-1]['entity'].name):
                reference['text_status'] = 'new'
            else:
                reference['text_status'] = 'given'

            if reference['sentence'] not in sentence_statuses:
                sentence_statuses[reference['sentence']] = []

            if reference['entity'].name not in sentence_statuses[reference['sentence']]:
                reference['sentence_status'] = 'new'
            else:
                reference['sentence_status'] = 'given'

            sentence_statuses[reference['sentence']].append(reference['entity'].name)

        return references

    def _realize_date(self, date):
        year, month, day = date.replace('\'', '').replace('\"', '').split('-')

        if day[-1] == '1':
            day = day + 'st'
        elif day[-1] == '2':
            day = day + 'nd'
        elif day[-1] == '3':
            day = day + 'rd'
        else:
            day = day + 'th'

        month = int(month)
        if month == 1:
            month = 'january'
        elif month == 2:
            month = 'february'
        elif month == 3:
            month = 'march'
        elif month == 4:
            month = 'april'
        elif month == 5:
            month = 'may'
        elif month == 6:
            month = 'june'
        elif month == 7:
            month = 'july'
        elif month == 8:
            month = 'august'
        elif month == 9:
            month = 'september'
        elif month == 10:
            month = 'october'
        elif month == 11:
            month = 'november'
        elif month == 12:
            month = 'december'
        else:
            month = str(month)

        return ' '.join([month, day, year])

    def _realize(self, prev_references, reference):
        entity = reference['entity'].name
        regex = '([0-9]{4})-([0-9]{2})-([0-9]{2})'
        if re.match(regex, entity) != None:
            return self._realize_date(entity)

        if reference['form'] == 'pronoun':
            isCompetitor, pronoun = self.prp.generate_major(prev_references, reference, self.data['pronouns'])

            if reference['no_pronoun']:
                return self.nnp.generate_major(reference, self.data['names'])
            elif isCompetitor:
                return self.dsc.generate_major(prev_references, reference, self.data['descriptions'])
            else:
                return pronoun
        elif reference['form'] == 'name':
            return self.nnp.generate_major(reference, self.data['names'])
        elif reference['form'] == 'description':
            return self.dsc.generate_major(prev_references, reference, self.data['descriptions'])
        elif reference['form'] == 'demonstrative':
            return self.dsc.generate_major(prev_references, reference, self.data['demonstratives'])

    def generate(self, template, entitymap):
        self.template = template.lower()
        self.entitymap = dict(map(lambda x: (x[0].lower(), x[1]), entitymap.items()))

        references = self._extract_references()
        references = form_choice.variation_bayes(references)

        references = sorted(references, key=lambda x: (x['sentence'], x['pos']))
        prev_references = []
        for reference in references:
            reference['realization'] = self._realize(prev_references, reference).lower()
            prev_references.append(reference)

        for reference in references:
            template = template.replace(reference['tag'], unicode(reference['realization']), 1)

        return template

    def run(self, fin, fout):
        entity_maps = p.load(open(os.path.join(fin, 'eval1.cPickle')))

        f = open(os.path.join(fin, 'eval1.bpe.de.output.postprocessed.dev'))
        templates = f.read().lower().split('\n')
        f.close()

        print len(templates), len(entity_maps)

        texts = []
        for i, template in enumerate(templates[:-1]):
            entity_map = entity_maps[i]

            text = self.generate(template, entity_map)
            texts.append(text)

            print template
            print text
            print 10 * '-'

        f = open(fout, 'w')
        for text in texts:
            f.write(text)
            f.write('\n')
        f.close()

if __name__ == '__main__':
    fin = '/home/tcastrof/cyber/data/nmt/delex/refs'
    fout = '/home/tcastrof/cyber/data/nmt/delex/refs/eval1.simple'
    simple = SimpleREG()
    simple.run(fin=fin, fout=fout)

    fout = '/home/tcastrof/cyber/data/nmt/delex/refs/eval1.out'
    reg = REG('/home/tcastrof/cyber/CyberTiCC/generator/reg/data.cPickle')
    reg.run(fin, fout)