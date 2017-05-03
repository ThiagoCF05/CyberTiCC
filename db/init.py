__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 02/05/2017
Description:
    This script aims to populate the database with training and dev sets of the WebNLG Challenge
"""

import os
import xml.etree.ElementTree as ET

from db import operations as db

class DBInit(object):
    def __init__(self):
        pass

    def run(self, dir, typeset):
        self.typeset = typeset

        for fname in os.listdir(dir):
            if fname != '.DS_Store':
                self.proc_file(os.path.join(dir, fname))

    def extract_entity_type(self, entity):
        aux = entity.split('^^')
        if len(aux) > 1:
            return aux[-1]

        aux = entity.split('@')
        if len(aux) > 1:
            return aux[-1]

        return 'wiki'

    def proc_file(self, fname):
        tree = ET.parse(fname)
        root = tree.getroot()

        entries = root.find('entries')

        for _entry in entries:
            entry = db.save_entry(docid=_entry.attrib['eid'], size=_entry.attrib['size'], category=_entry.attrib['category'], set=self.typeset)

            entities_type = []

            # Reading original triples to extract the entities type
            otripleset = _entry.find('originaltripleset')
            for otriple in otripleset:
                e1, pred, e2 = otriple.text.split('|')

                entity1_type = self.extract_entity_type(e1.strip())
                entity2_type = self.extract_entity_type(e2.strip())

                types = {'e1_type':entity1_type, 'e2_type':entity2_type}
                entities_type.append(types)

            # Reading modified triples to extract entities and predicate
            mtripleset = _entry.find('modifiedtripleset')
            for i, mtriple in enumerate(mtripleset):
                e1, pred, e2 = mtriple.text.split('|')

                entity1 = db.save_entity(e1.replace('\'', '').strip(), entities_type[i]['e1_type'])
                predicate = db.save_predicate(pred)
                entity2 = db.save_entity(e2.replace('\'', '').strip(), entities_type[i]['e2_type'])

                triple = db.save_triple(entity1, predicate, entity2)

                db.add_triple(entry, triple)

            # process lexical entries
            lexEntries = _entry.findall('lex')
            for lexEntry in lexEntries:
                lexEntry = db.save_lexEntry(docid=lexEntry.attrib['lid'], comment=lexEntry.attrib['comment'], text=lexEntry.text.strip())

                db.add_lexEntry(entry, lexEntry)

if __name__ == '__main__':
    db.clean()

    dbinit = DBInit()

    # TRAIN SET
    TRAIN_DIR = 'data/train'
    for dir in os.listdir(TRAIN_DIR):
        if dir != '.DS_Store':
            f = os.path.join(TRAIN_DIR, dir)
            print f
            dbinit.run(f, 'train')

    # DEV SET
    DEV_DIR = 'data/dev'
    for dir in os.listdir(DEV_DIR):
        if dir != '.DS_Store':
            f = os.path.join(DEV_DIR, dir)
            print f
            dbinit.run(f, 'dev')
