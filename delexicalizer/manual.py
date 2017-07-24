__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 24/07/2017
Description:
    Scripts based on the manual annotation of the corpus.
"""

import re
import reference_delex as ref_delex
import sys
sys.path.append('../')
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP

def get_references(out, entities):
    references = []
    for tag_entity in entities.iteritems():
        tag, entity = tag_entity
        refs, entity_removals = ref_delex.get_references(out, tag, entity)

        references.extend(refs)

    references = sorted(references, key=lambda x: (x['entity'], x['sentence'], x['pos']))

    sentence_statuses = {}
    for i, reference in enumerate(references):
        if i == 0 or (reference['entity'] != references[i-1]['entity']):
            reference['text_status'] = 'new'
        else:
            reference['text_status'] = 'given'

        if reference['sentence'] not in sentence_statuses:
            sentence_statuses[reference['sentence']] = []

        if reference['entity'] not in sentence_statuses[reference['sentence']]:
            reference['sentence_status'] = 'new'
        else:
            reference['sentence_status'] = 'given'

        sentence_statuses[reference['sentence']].append(reference['entity'])

    references = sorted(references, key=lambda x: x['general_pos'])
    return references

def extract_references(text, template, references):
    text = 'BEGIN BEGIN BEGIN ' + text
    template = 'BEGIN BEGIN BEGIN ' + template

    isOver = False
    while not isOver:
        stemplate = template.split()

        tag = ''
        pre_tag, pos_tag, i = [], [], 0
        for token in stemplate:
            i += 1
            if token.split('-')[0] in ['AGENT', 'PATIENT', 'BRIDGE']:
                tag = token
                for pos_token in stemplate[i:]:
                    if pos_token.split('-')[0] in ['AGENT', 'PATIENT', 'BRIDGE']:
                        break
                    else:
                        pos_tag.append(pos_token)
                break
            else:
                pre_tag.append(token)

        if tag == '':
            isOver = True
        else:
            regex = ' '.join(pre_tag).strip() + ' (.+?) ' + ' '.join(pos_tag).strip()
            f = re.findall(regex, text)

            if len(f) > 0:
                reference = f[0]
                template = template.replace(tag, reference, 1)

                for ref in references:
                    if ref['general_pos'] == i-4:
                        ref['realization'] = reference
                        break
    return references

proc = CoreNLP('parse')

f = open('report.txt')
doc = f.read()
f.close()

doc = doc.split((50*'*')+'\n')

for entry in doc:
    entry = entry.split('\n\n')

    _, entryId, size, semcategory = entry[0].replace('\n', '').split()

    entity_map = dict(map(lambda entity: entity.split(' | '), entry[2].replace('\nENTITY MAP\n', '').split('\n')))

    lexEntries = entry[3].replace('\nLEX\n', '').split('\n-')[:-1]

    for lex in lexEntries:
        if lex[0] == '\n':
            lex = lex[1:]
        lex = lex.split('\n')
        lexId = lex[0]

        out = proc.parse_doc(lex[1].replace('TEXT: ', '').strip())
        text = []
        for i, snt in enumerate(out['sentences']):
            text.extend(snt['tokens'])
        text = ' '.join(text)

        template = lex[2].replace('TEMPLATE: ', '')
        correct = lex[3].replace('CORRECT: ', '').strip()
        comment = lex[4].replace('COMMENT: ', '').strip()

        if comment in ['g', 'good']:
            template = template
        elif correct != '':
            template = correct

        out = proc.parse_doc(template)['sentences']
        references = get_references(out, entity_map)
        extract_references(text, template, references)