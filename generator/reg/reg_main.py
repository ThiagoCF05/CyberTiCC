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
sys.path.append('../')
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP
from db.model import *

import pronoun as prp
import proper_name as nnp
import description as dsc
import form_choice

class SimpleREG(object):
    def run(self, fname):
        entity_maps = p.load(open(os.path.join(fname, 'eval1.cPickle')))

        f = open(os.path.join(fname, 'eval1.bpe.de.output.postprocessed.dev'))
        texts = f.read().lower().split('\n')
        f.close()

        print len(texts), len(entity_maps)

        for i, text in enumerate(texts[:-1]):
            entity_map = entity_maps[i]

            for tag in entity_map:
                name = ' '.join(entity_map[tag].name.lower().name.replace('\'', '').replace('\"', '').split('_'))
                texts[i] = texts[i].replace(tag.lower(), name)

        f = open('eval1.out', 'w')
        for text in texts:
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
                        reference = {'syntax':'', 'sentence':i, 'pos':dep[2], 'tag':tag, 'entity':self.entitymap[tag]}
                        if 'nsubj' in dep[0] or 'nsubjpass' in dep[0]:
                            reference['syntax'] = 'np-subj'
                        elif 'nmod:poss' in dep[0] or 'compound' in dep[0]:
                            reference['syntax'] = 'subj-det'
                        else:
                            reference['syntax'] = 'np-obj'
                        references.append(reference)

        # Classify the references by text and sentence status
        references = sorted(references, key=lambda x: (x['entity'], x['sentence'], x['pos']))
        sentence_statuses = {}
        for i, reference in enumerate(references):
            if i == 0 or (reference['entity'] != references[i-1]['entity']):
                reference['text_status'] = 'new'
            else:
                reference['text_status'] = 'given'

            if reference['entity'] not in sentence_statuses:
                reference['sentence_status'] = 'new'
            else:
                reference['sentence_status'] = 'given'
            sentence_statuses[reference['entity']] = reference['sentence']

        return references

    def _realize(self, prev_references, reference):
        if reference['form'] == 'pronoun':
            isCompetitor, pronoun = self.prp.generate_major(prev_references, reference, self.data['pronouns'])

            if isCompetitor:
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
            print reference['tag'], reference['realization']
            print template
            template = str(template).encode('utf-8').replace(reference['tag'], str(reference['realization']).encode('utf-8'), 1)

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
    fout = '/home/tcastrof/cyber/data/nmt/delex/refs/eval1.out'

    simple = REG('/home/tcastrof/cyber/CyberTiCC/generator/reg/data.cPickle')
    simple.run(fin, fout)