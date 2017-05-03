__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 02/05/2017
Description:
    CRUD (Create, read, update and delete) operations in database
"""

import sys
sys.path.append('../')
from db.model import *

# Predicate operations
def save_predicate(name):
    predicate = Predicate(name=name)

    query = Predicate.objects(name=name)
    if query.count() == 0:
        predicate.save()
    else:
        predicate = query.get()
    return predicate

# Entity operations
def save_entity(name, type):
    entity = Entity(name=name, type=type)

    query = Entity.objects(name=name, type=type)
    if query.count() == 0:
        entity.save()
    else:
        entity = query.get()
    return entity

# Triple operations
def save_triple(e1, pred, e2):
    triple = Triple(agent=e1, predicate=pred, patient=e2)

    query = Triple.objects(agent=e1, predicate=pred, patient=e2)
    if query.count() == 0:
        triple.save()
    else:
        triple = query.get()
    return triple

# Lexical entry operations
def save_lexEntry(docid, comment, text):
    lexEntry = Lex(docid=docid, comment=comment, text=text)

    query = Lex.objects(docid=docid, comment=comment, text=text)
    if query.count() == 0:
        lexEntry.save()
    else:
        lexEntry = query.get()
    return lexEntry

# Entry operations
def save_entry(docid, size, category, set):
    entry = Entry(docid=docid, size=size, category=category, set=set)

    query = Entry.objects(docid=docid, size=size, category=category)
    if query.count() == 0:
        entry.save()
    else:
        entry = query.get()
    return entry

def add_triple(entry, triple):
    query = Entry.objects(triples=triple)

    if query.count() == 0:
        entry.update(add_to_set__triples=[triple])

def add_lexEntry(entry, lexEntry):
    query = Entry.objects(texts=lexEntry)

    if query.count() == 0:
        entry.update(add_to_set__texts=[lexEntry])

# Clean database
def clean():
    Entry.objects().delete()
    Triple.objects().delete()
    Lex.objects().delete()
    Entity.objects().delete()
    Predicate.objects().delete()