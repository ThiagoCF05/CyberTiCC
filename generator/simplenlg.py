
import sys
sys.path.append('../')
from db.model import *
import db.operations as dbop
import nltk
import operator
import utils

if __name__ == '__main__':
    deventries = Entry.objects(size=2, set='dev')

    for deventry in deventries:
        # entity and predicate mapping
        entitymap, predicates = utils.map_entities(triples=deventry.triples)

        trainentries = Entry.objects(size=len(deventry.triples), set='train')
        for i, triple in enumerate(deventry.triples):
            trainentries = filter(lambda entry: entry.triples[i].predicate.name == triple.predicate.name, trainentries)

        # extract templates
        templates = []
        for entry in trainentries:
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
        print 'Predicate:', predicates
        for item in sorted(templates.items(), key=operator.itemgetter(1), reverse=True)[:5]:
            template, freq = item
            print template, freq
        print 10 * '-'