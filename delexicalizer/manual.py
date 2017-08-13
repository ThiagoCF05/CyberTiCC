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
import db.operations as dbop

from db.model import *
from stanford_corenlp_pywrapper import CoreNLP

class ManualDelexicalizer(object):
    def __init__(self, fname, _set='train'):
        self.proc = CoreNLP('parse')
        self._set = _set

        f = open(fname)
        doc = f.read()
        f.close()

        doc = doc.split((50*'*')+'\n')

        print 'Doc size: ', len(doc)

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
                text = lex[1].replace('TEXT: ', '').strip()
                template = lex[2].replace('TEMPLATE: ', '')
                correct = lex[3].replace('CORRECT: ', '').strip()
                comment = lex[4].replace('COMMENT: ', '').strip()

                if comment in ['g', 'good']:
                    print template
                    print 10 * '-'
                    self.update_template(entryId, size, semcategory, _set, lexId, template)
                    references = self.process_references(text, template, entity_map)
                    self.save_references(references)
                elif correct != '' and comment != 'wrong':
                    print correct
                    print 10 * '-'
                    self.update_template(entryId, size, semcategory, _set, lexId, correct)
                    references = self.process_references(text, correct, entity_map)
                    self.save_references(references)

    def _get_references_info(self, out, entities):
        '''
        Get syntactic position, text and sentence status of the references based on dependency parser
        :param out: stanford corenlp result
        :param entities: tag - wikipedia id mapping
        :return:
        '''
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

    def _get_refexes(self, text, template, references):
        '''
        Extract referring expressions for each reference overlapping text and template
        :param text: original text
        :param template: template (delexicalized text)
        :param references: references
        :return:
        '''
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
                regex = re.escape(' '.join(pre_tag[-3:]).strip()) + ' (.+?) ' + re.escape(' '.join(pos_tag[:3]).strip())
                f = re.findall(regex, text)

                if len(f) > 0:
                    refex = f[0]
                    template = template.replace(tag, refex, 1)

                    ref_type = 'name'
                    if refex.lower().strip() in ['he', 'his', 'him', 'she', 'hers', 'her', 'it', 'its', 'they', 'theirs', 'them']:
                        ref_type = 'pronoun'
                    elif refex.lower().strip().split()[0] in ['the', 'a', 'an']:
                        ref_type = 'description'
                    elif refex.lower().strip().split()[0] in ['this', 'these', 'that', 'those']:
                        ref_type = 'demonstrative'

                    for ref in references:
                        if ref['tag'] == tag and 'refex' not in ref:
                            ref['refex'] = refex
                            ref['reftype'] = ref_type
                            break
                else:
                    template = template.replace(tag, ' ', 1)
        return references

    def update_template(self, entryId, size, semcategory, _set, lexId, template):
        entry = Entry.objects(docid=entryId, size=size, category=semcategory, set=_set).first()

        for lexEntry in entry.texts:
            if lexEntry.docid == lexId:
                dbop.insert_template(lexEntry, template, 'manual')
                break

    def save_references(self, references):
        '''
        Save references and referring expressions extracted from the manual annotation
        :param references:
        :return:
        '''
        for reference in references:
            if 'refex' in reference:
                ref = dbop.save_reference(entity=reference['entity'],
                                          syntax=reference['syntax'],
                                          text_status=reference['text_status'],
                                          sentence_status=reference['sentence_status'])

                dbop.add_refex(ref, reference['reftype'], reference['refex'], 'manual')

    def process_references(self, text, template, entities):
        '''
        Obtain information of references and their referring expressions
        :param text:
        :param template:
        :param entities:
        :return:
        '''
        out = self.proc.parse_doc(text)
        text = []
        for i, snt in enumerate(out['sentences']):
            text.extend(snt['tokens'])
        text = ' '.join(text).replace('-LRB- ', '(').replace(' -RRB-', ')').strip()

        out = self.proc.parse_doc(template)['sentences']
        references = self._get_references_info(out, entities)
        references = self._get_refexes(text, template, references)
        return references

if __name__ == '__main__':
    dbop.clean_delex()
    ManualDelexicalizer('report.txt')