__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 20/06/2017
Description:
    This script aims to generate references in the description and demonstrative forms
"""

class DescriptionGeneration(object):
    def __init__(self):
        pass

    def generate(self, prev_references, reference, form='description'):
        '''
        :param prev_references: previous realized references
        :param reference: reference to be realized
        :return: realization
        '''

        entity = reference['entity']
        description = entity.description
        # Return the proper name of the entity if description is not available in the database
        if description == '':
            name = ' '.join(entity.name.replace('\'', '').replace('\"', '').split('_'))
            return name
        else:
            if form == 'demonstrative':
                description = description.split()
                description[0] = 'this'
                description = ' '.join(description)

            # Check for a competitor
            isCompetitor = False
            for prev_reference in prev_references:
                if prev_reference['entity'].name != entity.name and prev_reference['realization'] == description:
                    isCompetitor = True
                    break

            # If it is a competitor, return the name of the entity
            if not isCompetitor:
                return description
            else:
                name = ' '.join(entity.name.replace('\'', '').replace('\"', '').split('_'))
                return name