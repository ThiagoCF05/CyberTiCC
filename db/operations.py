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
from mongoengine.queryset.visitor import Q

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
def save_entity(name, type, ner, category, description):
    entity = Entity(name=name, type=type)

    query = Entity.objects(name=name, type=type, ner=ner, category=category, description=description)
    if query.count() == 0:
        entity.save()
    else:
        entity = query.get()
    return entity

def get_entity(name):
    return Entity.objects(name=name).first()

def add_description(entity, description):
    entity.modify(set__description=description)

def add_ner(entity, ner):
    entity.modify(set__ner=ner)

def add_category(entity, category):
    entity.modify(set__category=category)

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
def save_lexEntry(docid, comment, text, parse_tree, template=''):
    lexEntry = Lex(docid=docid, comment=comment, text=text, template=template, parse_tree=parse_tree)
    lexEntry.save()
    return lexEntry

def insert_template(lexEntry, template):
    lexEntry.modify(set__template=template)
    return lexEntry

# Template operations
def save_template(category, triples, template):
    template = Entry(category=category, triples=triples, template=template)
    template.save()
    return template

# Entry operations
def save_entry(docid, size, category, set):
    entry = Entry(docid=docid, size=size, category=category, set=set)

    query = Entry.objects(docid=docid, size=size, category=category, set=set)
    if query.count() == 0:
        entry.save()
    else:
        entry = query.get()
    return entry

def add_triple(entry, triple):
    query = Entry.objects(Q(id=entry.id) & Q(triples=triple))

    if query.count() == 0:
        entry.update(add_to_set__triples=[triple])

def add_lexEntry(entry, lexEntry):
    query = Entry.objects(Q(id=entry.id) & Q(texts=lexEntry))

    if query.count() == 0:
        entry.update(add_to_set__texts=[lexEntry])

# Reference operations
def save_reference(entity, syntax, text_status, sentence_status):
    if type(entity) == str or type(entity) == unicode:
        entity = Entity.objects(name=entity).get()
    reference = Reference(entity=entity, syntax=syntax, text_status=text_status, sentence_status=sentence_status)

    query = Reference.objects(entity=entity, syntax=syntax, text_status=text_status, sentence_status=sentence_status)

    if query.count() == 0:
        reference.save()
    else:
        reference = query.get()
    return reference

def add_refex(reference, refex):
    reference.update(add_to_set__refexes=[refex])

# Referring expression
def save_refex(reftype, refex):
    entry = Refex(ref_type=reftype, refex=refex)

    query = Refex.objects(ref_type=reftype, refex=refex)
    if query.count() == 0:
        entry.save()
    else:
        entry = query.get()
    return entry

# Clean database
def clean():
    Entry.objects().delete()
    Triple.objects().delete()
    Reference.objects().delete()
    Refex.objects().delete()
    Lex.objects().delete()
    Entity.objects().delete()
    Predicate.objects().delete()

# Clean delex information
def clean_delex():
    Reference.objects().delete()
    Refex.objects().delete()
    Lex.objects.update(template='')