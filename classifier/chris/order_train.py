import json
import re
from collections import Counter
from nltk.util import ngrams
import numpy as np
import itertools
import numpy
import operator

def tripletransform(triple):
    newtriple = triple.split(' | ')
    # Use NLTK to generate trigrams, bigrams and unigrams from the triple
    trigrams = ngrams(newtriple, 3)
    trigramscounter = dict(Counter(trigrams))
    bigrams = ngrams(newtriple, 2)
    bigramscounter = dict(Counter(bigrams))
    unigrams = ngrams(newtriple, 1)
    unigramscounter = dict(Counter(unigrams))
    # Make a combined list of the bigrams and unigrams
    combine = unigramscounter.copy()
    combine.update(bigramscounter)
    combine.update(trigramscounter)
    newcombine = {}
    # Convert the tuple keys of the dictionary to strings
    for i in combine:
        newi = list(i)
        newi = " ".join(newi)
        newcombine.update({newi: combine[i]})
    return newcombine

def labelonly(instancelist):
    #Function that takes the list of triples for an instance and returns the first value (the relationship label)
    newinstancelist = []
    for instance in instancelist:
        newtriple = instance.split(' | ')
        newinstancelist.append(newtriple[1])
    return newinstancelist

def trainfunction(trainset):
    uniquelist = []
    totaldict = {}
    totallabels = 0
    #Search every instance
    for instance in trainset:
        #And every label in the instance
        for label in instance:
            #Get a list containing only the unique mentions by searching if the label is in the uniquelist
            if label not in uniquelist:
                uniquelist.append(label)

    #Now let's search for every unique label
    for label in uniquelist:
        #If they are present in an instance
        for instance in trainset:
            #If they are, let's add them to the totaldict
            if label in instance:
                #The totaldict has the layout label: {times first position: <number>, times second position: <number>, ..., sum of position: <number>, number of occurrences in terms of instances: <number>, total number of occurrences: <number>]
                #Get a list containing all positions (+ 1) mentioning the label in the instance
                dictpositions = [i + 1 for i, j in enumerate(instance) if j == label]
                try:
                    labelcount = instance.count(label)
                except AttributeError:
                    print(instance)
                    sys.exit(1)
                totallabels += labelcount
                #Get the sum, occurences per instance, total occurrences in this case
                newdict = {'sum': sum(dictpositions), 'occurrences per instance': 1, 'total occurrences': labelcount}
                #And give the total occurrences in this case a separate dict entry
                labelcountx = str(labelcount) + 'x'
                newdict.update({labelcountx: 1})
                #Now add the positions found to the newdict
                for position in dictpositions:
                    newdict.update({position: 1})
                # If the label is in the totaldict already, get the dict value dict and combine that with the existing dict
                if label in totaldict:
                    totaldict[label] = dict(Counter(totaldict[label]) + Counter(newdict))
                else:
                    totaldict.update({label: newdict})

    #Cool, we've got a dict that gets information about the position and frequency of every label
    #Some labels are more frequent than others, it is certainly possible that some labels in the test set are not in the training set.
    #So let's make another category, we call 'misc'. This category is based on the bottom 0.1% labels in terms of frequency.
    #If a label in the test set is not present in the training set, we call that label misc and base it on the generated misc
    #category

    ## DON'T USE AVERAGE, USE SOMETHING LIKE POSITION FREQUENCY!!!
    totaldict.update({'misc': {}})
    for label in totaldict:
        if totaldict[label]['total occurrences'] < int(totallabels /1000):
            totaldict['misc'] = dict(Counter(totaldict[label]) + Counter(totaldict['misc']))
    #We have the total amount of mentioned, and the sum of all positions. So, let's calculate the position averages!
    for label in totaldict:
        for item in totaldict[label]:
            #Get the probabilities per position by dividing the positional occurrences by the total occurrences
            if (item != 'occurrences per instance') and (item != 'total occurrences') and not (re.search(r'^\dx$', str(item))):
                totaldict[label][item] = totaldict[label][item] / totaldict[label]['total occurrences']
            #The average usages of a label in one instance is represented by keys such as '1x', '2x', 3x'
            #Get the average amount of label usage by dividing them by the occurrences per instance
            elif re.search(r'^\dx$', str(item)):
                totaldict[label][item] = totaldict[label][item] / totaldict[label]['occurrences per instance']
        #Get the average amount of occurrences per instance by dividing the total occurrences by the occurrences per instance
        totaldict[label]['occurrences per instance'] = totaldict[label]['total occurrences'] / totaldict[label]['occurrences per instance']

    return totaldict

with open('../data/train_order.json') as json_data:
    d1 = json.load(json_data)

with open('../data/dev_order.json') as json_data:
    d2 = json.load(json_data)

d = d1 + d2

sortedlist = []
tripleslist = []
#Get a separate list for the triples and sorted parts of the json file
#And convert them to the relation-label only
for instance in d:
    sorted, triples = instance['sorted'], instance['triples']
    sorted, triples = labelonly(sorted), labelonly(triples)
    sortedlist.append(sorted)
    tripleslist.append(triples)

orderdict = trainfunction(sortedlist)

with open('../data/freq_order.json', 'w') as json_data:
    json.dump(orderdict, json_data)