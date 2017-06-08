__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 07/06/2017
Description:
    Main code for Referring expression generation
"""

import sys
sys.path.append('../')
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP

import pronoun as prp
import proper_name as nnp
import form_choice

class REG(object):
    def __init__(self):
        self.proc = CoreNLP('parse')
        self.nnp = nnp.ProperNameGeneration()
        self.prp = prp.Pronominalization()

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

    def _realize(self, reference):
        if reference['form'] == 'pronoun':
            return self.prp.generate(reference)
        elif reference['form'] in ['pronoun', 'name', 'description', 'demonstrative']:
            return self.nnp.generate(reference)

    def generate(self, template, entitymap):
        self.template = template
        self.entitymap = entitymap

        references = self._extract_references()
        references = form_choice.variation_bayes(references)

        for reference in references:
            reference['realization'] = self._realize(reference)

        references = sorted(references, key=lambda x: (x['sentence'], x['pos']))
        for reference in references:
            template = template.replace(reference['tag'], reference['realization'], 1)

        return template