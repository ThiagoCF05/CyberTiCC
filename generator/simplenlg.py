
import sys
sys.path.append('../')
from db.model import *
import db.operations as dbop
import nltk
import operator
import utils

if __name__ == '__main__':
    deventries = Entry.objects(set='dev')

    f = open('out.txt', 'w')
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

        f.write(10 * '-')
        f.write('\n')
        f.write('Entities: ' + str(entitymap))
        f.write('\n')
        f.write('Predicate: ' + str(predicates))
        f.write('\n')
        for item in sorted(templates.items(), key=operator.itemgetter(1), reverse=True)[:5]:
            template, freq = item
            for tag, name in entitymap.iteritems():
                template = template.replace(tag, ' '.join(name.split('_')))
            f.write(template.encode('utf-8') + ' ' + str(freq))
            f.write('\n')
        f.write(10 * '-')
        f.write('\n')
    f.close()
