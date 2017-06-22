import copy

# TO DO: bring entities with references
def map_entities(triples):
    entity_map, nagents, npatients, nbridges = {}, 1, 1, 1
    predicates = []
    for triple in triples:
        agent = triple.agent
        predicate = triple.predicate
        patient = triple.patient

        predicates.append(predicate)

        f = filter(lambda tag: entity_map[tag].name == agent.name and 'PATIENT' in tag, entity_map)
        if len(f) > 0:
            original_tag = f[0]
            original_id = int(original_tag.split('-')[1])
            new_tag = 'BRIDGE-' + str(nbridges)

            entity_map[str(new_tag)] = entity_map[str(original_tag)]
            del entity_map[str(original_tag)]

            nbridges += 1
            new_entity_map = {}
            for tag in entity_map.keys():
                role, id = tag.split('-')
                id = int(id)
                if role == 'PATIENT' and id > original_id:
                    new_entity_map[role+'-'+str(id-1)] = entity_map[str(tag)]
                else:
                    new_entity_map[str(tag)] = entity_map[str(tag)]
            entity_map = copy.deepcopy(new_entity_map)
            npatients -= 1
        elif agent.name not in map(lambda entity: entity.name, entity_map.values()):
            tag = 'AGENT-' + str(nagents)
            entity_map[str(tag)] = agent
            nagents += 1

        f = filter(lambda tag: entity_map[tag].name == patient.name and 'AGENT' in tag, entity_map)
        if len(f) > 0:
            original_tag = f[0]
            original_id = int(original_tag.split('-')[1])
            new_tag = 'BRIDGE-' + str(nbridges)

            entity_map[str(new_tag)] = entity_map[str(original_tag)]
            del entity_map[str(original_tag)]

            nbridges += 1
            new_entity_map = {}
            for tag in entity_map.keys():
                role, id = tag.split('-')
                id = int(id)
                if role == 'AGENT' and id > original_id:
                    new_entity_map[role+'-'+str(id-1)] = entity_map[str(tag)]
                else:
                    new_entity_map[str(tag)] = entity_map[str(tag)]
            entity_map = copy.deepcopy(new_entity_map)
            nagents -= 1
        elif patient.name not in map(lambda entity: entity.name, entity_map.values()):
            tag = 'PATIENT-' + str(npatients)
            entity_map[str(tag)] = patient
            npatients += 1
    return entity_map, predicates

def entity2tag(entity_map):
    return dict(map(lambda x: (x[1], x[0]), entity_map.items()))

def get_e2f(fname):
    f = open(fname)
    doc = f.read().split('\n')
    f.close()

    e2f = {}
    for row in doc:
        aux = row.split()
        if len(aux) == 3:
            wiki, word, prob = aux

            if wiki not in e2f:
                e2f[wiki] = {}

            e2f[wiki][word] = float(prob)
    return e2f

def write_references(fname, refs):
    f1 = open(fname+'1', 'w')
    f2 = open(fname+'2', 'w')
    f3 = open(fname+'3', 'w')
    f4 = open(fname+'4', 'w')
    f5 = open(fname+'5', 'w')

    for references in refs:
        f1.write(references[0].encode('utf-8'))
        f1.write('\n')

        if len(references) >= 2:
            f2.write(references[1].encode('utf-8'))
        f2.write('\n')

        if len(references) >= 3:
            f3.write(references[2].encode('utf-8'))
        f3.write('\n')

        if len(references) >= 4:
            f4.write(references[3].encode('utf-8'))
        f4.write('\n')

        if len(references) >= 5:
            f5.write(references[4].encode('utf-8'))
        f5.write('\n')

    f1.close()
    f2.close()
    f3.close()
    f4.close()
    f5.close()

def write_hyps(fname, hyps):
    f = open(fname, 'w')
    for hyp in hyps:
        f.write(hyp.encode('utf-8'))
        f.write('\n')
    f.close()