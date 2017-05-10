

# TO DO: bring entities with references
def map_entities(triples):
    entity_map, nagents, npatients = {}, 1, 1
    predicates = []
    for triple in triples:
        agent = triple.agent.name
        predicate = triple.predicate.name
        patient = triple.patient.name

        predicates.append(predicate)

        f = filter(lambda tag: entity_map[tag] == agent, entity_map)
        if len(f) == 0:
            tag = 'AGENT-' + str(nagents)
            entity_map[str(tag)] = agent
            nagents += 1

        f = filter(lambda tag: entity_map[tag] == patient, entity_map)
        if len(f) == 0:
            tag = 'PATIENT-' + str(npatients)
            entity_map[str(tag)] = patient
            npatients += 1
    return entity_map, predicates