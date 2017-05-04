__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 03/05/2017
Description:
    Delexicalizing entities from the text based on the triples
    Method Simple Match
"""

import sys
sys.path.append('../')
from db.model import *
import db.operations as dbop
import copy
import re

if __name__ == '__main__':
    dbop.clean_delex()
    entries = Entry.objects(size=1, set='train')

    for entry in entries:
        print entry.docid, '\r',
        entity_map, nagents, npatients = {}, 1, 1
        for triple in entry.triples:
            agent = triple.agent.name
            predicate = triple.predicate.name
            patient = triple.patient.name

            f = filter(lambda tag: entity_map[tag] == agent, entity_map)
            if len(f) == 0:
                tag = 'AGENT-' + str(nagents)
                entity_map[str(tag)] = dbop.get_entity(agent)
                nagents += 1

            f = filter(lambda tag: entity_map[tag] == patient, entity_map)
            if len(f) == 0:
                tag = 'PATIENT-' + str(npatients)
                entity_map[str(tag)] = dbop.get_entity(patient)
                npatients += 1

        templates = []
        lexEntries = entry.texts
        for lexEntry in lexEntries:
            text = lexEntry.text

            template = copy.copy(text)
            for tag, entity in entity_map.iteritems():
                simple_match = ' '.join(entity.name.replace('\'', '').split('_'))

                if len(re.findall(simple_match, template)) > 0:
                    template = template.replace(simple_match, tag)

                    reference = dbop.save_reference(tag, entity)
                    dbop.add_reference(lexEntry, reference)

            dbop.insert_template(lexEntry, template)