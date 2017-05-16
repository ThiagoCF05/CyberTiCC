

# TO DO: bring entities with references
def map_entities(triples):
    entity_map, nagents, npatients, nbridges = {}, 1, 1, 1
    predicates = []
    for triple in triples:
        agent = triple.agent.name
        predicate = triple.predicate.name
        patient = triple.patient.name

        predicates.append(predicate)

        f = filter(lambda tag: entity_map[tag] == agent and 'PATIENT' in tag, entity_map)
        if len(f) > 0:
            original_tag = f[0]
            original_id = int(original_tag.split('-')[1])
            new_tag = 'BRIDGE-' + str(nbridges)

            entity_map[str(new_tag)] = entity_map[str(original_tag)]
            del entity_map[str(original_tag)]

            nbridges += 1
            for tag in entity_map.keys():
                role, id = tag.split('-')
                id = int(id)
                if role == 'PATIENT' and id > original_id:
                    entity_map[role+'-'+str(id-1)] = entity_map[str(tag)]
                    del entity_map[str(tag)]
            npatients -= 1
        elif agent not in entity_map.values():
            tag = 'AGENT-' + str(nagents)
            entity_map[str(tag)] = agent
            nagents += 1

        f = filter(lambda tag: entity_map[tag] == patient and 'AGENT' in tag, entity_map)
        if len(f) > 0:
            original_tag = f[0]
            original_id = int(original_tag.split('-')[1])
            new_tag = 'BRIDGE-' + str(nbridges)

            entity_map[str(new_tag)] = entity_map[str(original_tag)]
            del entity_map[str(original_tag)]

            nbridges += 1
            for tag in entity_map.keys():
                role, id = tag.split('-')
                id = int(id)
                if role == 'AGENT' and id > original_id:
                    entity_map[role+'-'+str(id-1)] = entity_map[str(tag)]
                    del entity_map[str(tag)]
            nagents -= 1
        elif patient not in entity_map.values():
            tag = 'PATIENT-' + str(npatients)
            entity_map[str(tag)] = patient
            npatients += 1
    return entity_map, predicates

def entity2tag(entity_map):
    return dict(map(lambda x: (x[1], x[0]), entity_map.items()))