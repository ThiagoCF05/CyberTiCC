__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 08/08/2017
Description:
    Compute frequency of referring expressions for each reference condition
"""

import cPickle as p
import nltk
import sys
sys.path.append('../')
from db.model import *

lemma = {
    'he':'he', 'his':'he',
    'she':'she', 'her':'she', 'hers':'she',
    'it':'it', 'its':'it',
    'we':'we', 'our':'we', 'ours':'we', 'us':'we',
    'they':'they', 'their':'they', 'theirs':'they', 'them':'they'
}
pronouns, names, descriptions, demonstratives = {}, {}, {}, {}

refs = Reference.objects()

entities = Entity.objects()

for entity in entities:
    pronouns[entity.name] = []
    bnames, bdescriptions, bdemonstratives = [], [], [], []

    for syntax in ['np-subj', 'np-obj', 'subj-det']:
        for text_status in ['new', 'given']:
            for sentence_status in ['new', 'given']:
                reference = Reference.objects(entity=entity, syntax=syntax, text_status=text_status, sentence_status=sentence_status)

                names[(syntax, text_status, sentence_status, entity)] = []
                descriptions[(syntax, text_status, sentence_status, entity)] = []
                demonstratives[(syntax, text_status, sentence_status, entity)] = []

                if reference.count() > 0:
                    reference = reference.first()

                    for refex in reference.refexes:
                        reftype = refex.ref_type
                        reg = refex.refex.strip().lower()
                        if reftype == 'pronoun' and reg in lemma:
                            pronouns[entity.name].append(reg)
                        elif reftype == 'name':
                            names[(syntax, text_status, sentence_status, entity)].append(reg)
                        elif reftype == 'description':
                            descriptions[(syntax, text_status, sentence_status, entity)].append(reg)
                        elif reftype == 'demonstrative':
                            demonstratives[(syntax, text_status, sentence_status, entity)].append(reg)

                if len(names[(syntax, text_status, sentence_status, entity)]) == 0:
                    bnames.append((syntax, text_status, sentence_status, entity))
                if len(descriptions[(syntax, text_status, sentence_status, entity)]) == 0:
                    bdescriptions.append((syntax, text_status, sentence_status, entity))
                if len(demonstratives[(syntax, text_status, sentence_status, entity)]) == 0:
                    bdemonstratives.append((syntax, text_status, sentence_status, entity))

            # First backoff
            reference = Reference.objects(entity=entity, syntax=syntax, text_status=text_status)
            if reference.count() > 0:
                reference = reference.first()

                for refex in reference.refexes:
                    reftype = refex.ref_type
                    reg = refex.refex.strip().lower()
                    if reftype == 'name':
                        for key in bnames:
                            names[key].append(reg)
                        bnames = []
                    elif reftype == 'description':
                        for key in bdescriptions:
                            descriptions[key].append(reg)
                        bdescriptions = []
                    elif reftype == 'demonstrative':
                        for key in bdemonstratives:
                            demonstratives[key].append(reg)
                        bdemonstratives = []

        # Second backoff
        reference = Reference.objects(entity=entity, syntax=syntax)
        if reference.count() > 0:
            reference = reference.first()

            for refex in reference.refexes:
                reftype = refex.ref_type
                reg = refex.refex.strip().lower()
                if reftype == 'name':
                    for key in bnames:
                        names[key].append(reg)
                    bnames = []
                elif reftype == 'description':
                    for key in bdescriptions:
                        descriptions[key].append(reg)
                    bdescriptions = []
                elif reftype == 'demonstrative':
                    for key in bdemonstratives:
                        demonstratives[key].append(reg)
                    bdemonstratives = []


    # Third backoff
    reference = Reference.objects(entity=entity)
    if reference.count() > 0:
        reference = reference.first()

        for refex in reference.refexes:
            reftype = refex.ref_type
            reg = refex.refex.strip().lower()
            if reftype == 'name':
                for key in bnames:
                    names[key].append(reg)
                bnames = []
            elif reftype == 'description':
                for key in bdescriptions:
                    descriptions[key].append(reg)
                bdescriptions = []
            elif reftype == 'demonstrative':
                for key in bdemonstratives:
                    demonstratives[key].append(reg)
                bdemonstratives = []

for entity in pronouns:
    pronouns[entity] = sorted(nltk.FreqDist(pronouns[entity]).items(), key=lambda x:x[1], reverse=True)[:2]

for key in names:
    names[key] = sorted(nltk.FreqDist(names[key]).items(), key=lambda x:x[1], reverse=True)[:2]

for key in descriptions:
    descriptions[key] = sorted(nltk.FreqDist(descriptions[key]).items(), key=lambda x:x[1], reverse=True)[:2]

for key in demonstratives:
    demonstratives[key] = sorted(nltk.FreqDist(demonstratives[key]).items(), key=lambda x:x[1], reverse=True)[:2]

references = {'pronouns':pronouns, 'names':names, 'descriptions':descriptions, 'demonstratives':demonstratives}
p.dump(references, open('data.cPickle', 'w'))