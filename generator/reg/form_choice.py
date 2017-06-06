__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 02/06/2017
Description:
    Choice of referential form model
"""

import cPickle as p
import operator
from random import shuffle

DISTRIBUTIONS = p.load(open('form_distributions.cPickle'))

# text-new -> name / text-old -> pronoun
def rule_form_choice(text_status):
    if text_status == 'new':
        return 'name'
    else:
        return 'pronoun'

def regular_bayes(references, distributions=DISTRIBUTIONS):
    forms = []
    for reference in references:
        X = (reference.syntax, reference.text_status, reference.sentence_status)

        form = sorted(distributions[X].items(), key=operator.itemgetter(1), reverse=True)[0][0]
        forms.append(form)
    return forms

def variation_bayes(references, distributions=DISTRIBUTIONS):
    def group():
        g = {}
        for reference in references:
            X = (reference.syntax, reference.text_status, reference.sentence_status)
            if X not in g:
                g[X] = {'distribution': distributions[X], 'references':[]}
            g[X]['references'].append(reference)
        return g

    def choose_form(_references, distribution):
        result = {}

        size = len(_references)
        for form in distribution:
            distribution[form] = size * distribution[form]

        # print distribution
        shuffle(_references)
        for reference in _references:
            form = sorted(distribution.items(), key=operator.itemgetter(1), reverse=True)[0][0]
            result[reference.id] = form

            distribution[form] -= 1
        return result

    groups = group()
    forms = {}
    for g in groups:
        f = choose_form(groups[g]['references'], groups[g]['distribution'])
        forms.update(f)
    return forms