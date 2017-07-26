__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 24/07/2017
Description:
    Scripts for reference details (syntactic position and referential status) and remove determiners and compounds
"""

import sys
sys.path.append('../')
import db.operations as dbop

def get_references(out, tag, entity):
    '''
    get reference details (syntactic position and referential status) and remove determiners and compounds
    :param out: stanford corenlp result
    :param tag: tag (agent, patient or bridge)
    :param entity: wikipedia id
    :return:
    '''
    references = []
    removals = {}
    general_pos = 0
    for i, snt in enumerate(out):
        deps = snt['deps_cc']
        visited_tokens = []
        for dep in deps:
            # get syntax
            if snt['tokens'][dep[2]] == tag and dep[2] not in visited_tokens:
                visited_tokens.append(dep[2])
                reference = {'syntax':'', 'sentence':i, 'pos':dep[2], 'general_pos':general_pos+dep[2], 'entity':entity, 'tag':tag, 'determiner':'', 'compounds':[]}
                if 'nsubj' in dep[0] or 'nsubjpass' in dep[0]:
                    reference['syntax'] = 'np-subj'
                elif 'nmod:poss' in dep[0] or 'compound' in dep[0]:
                    reference['syntax'] = 'subj-det'
                else:
                    reference['syntax'] = 'np-obj'
                references.append(reference)
        general_pos += len(snt['tokens'])

    for i, snt in enumerate(out):
        deps = snt['deps_cc']
        removals[i] = []
        for dep in deps:
            # mark compounds and determiners
            if snt['tokens'][dep[1]] == tag:
                if dep[0] == 'det':
                    for j, reference in enumerate(references):
                        if reference['sentence'] == i and reference['pos'] == dep[1]:
                            references[j]['determiner'] = snt['tokens'][dep[2]].lower()
                            removals[i].append(dep[2])

                if dep[0] == 'compound':
                    for j, reference in enumerate(references):
                        if reference['sentence'] == i and reference['pos'] == dep[1] \
                                and 'AGENT' not in snt['tokens'][dep[2]] \
                                and 'PATIENT' not in snt['tokens'][dep[2]] \
                                and 'BRIDGE' not in snt['tokens'][dep[2]]:
                            references[j]['compounds'].append((dep[2], snt['tokens'][dep[2]]))
                            removals[i].append(dep[2])

    return references, removals

def parse_references(references):
    '''
    Parse and save references (referential status)
    :param references:
    :return:
    '''
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

        ref = dbop.save_reference(entity=reference['entity'],
                                  syntax=reference['syntax'],
                                  text_status=reference['text_status'],
                                  sentence_status=reference['sentence_status'])

        refex = dbop.save_refex(reftype=reference['reftype'], refex=reference['refex'])
        dbop.add_refex(ref, refex)