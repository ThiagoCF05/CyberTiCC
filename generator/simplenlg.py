
import sys
sys.path.append('../')
from db.model import *
import db.operations as dbop
import nltk
import operator
import utils

if __name__ == '__main__':
    deventries = Entry.objects(size=1, set='dev')

    for deventry in deventries:
        entitymap, predicates = utils.map_entities(triples=deventry.triples)

        pred = predicates[0]

        # search triples with the predicate
        predicate = Predicate.objects(name=pred).get()
        ftriples = Triple.objects(predicate=predicate)

        # search entries with the triples
        entries = []
        for ftriple in ftriples:
            entries.extend(Entry.objects(set='train', size=1, triples=ftriple))

        # extract templates
        templates = []
        for entry in entries:
            for lexEntry in entry.texts:
                template = lexEntry.template

                entitiesPresence = True
                for tag in entitymap:
                    if tag not in template:
                        entitiesPresence = False
                        break
                if entitiesPresence:
                    templates.append(template)

        templates = nltk.FreqDist(templates)

        print 10 * '-'
        print 'Entities:', entitymap
        print 'Predicate:', pred
        for item in sorted(templates.items(), key=operator.itemgetter(1), reverse=True)[:4]:
            template, freq = item
            print template, freq
        print 10 * '-'