__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 03/05/2017
Description:
    This script aims to evaluate the quality of the delexicalizers by measuring accuracy
"""

import sys
sys.path.append('../')
import utils
from db.model import *

def evaluate(verbose=False):
    entries = Entry.objects(size=1, set='train')

    # evaluation
    num, dem = 0, 0

    for entry in entries:
        entity_map, predicates= utils.map_entities(entry.triples)

        for lexEntry in entry.texts:
            local_num = 0
            dem += len(entity_map.keys())

            template = lexEntry.template
            for tag in entity_map:
                if tag in template:
                    local_num += 1
                    num += 1

            if local_num != len(entity_map.keys()) and verbose:
                print entity_map
                print lexEntry.template
                print 20 * '-'


    print 'Evaluation: ', (float(num) / dem)

if __name__ == '__main__':
    evaluate(verbose=False)