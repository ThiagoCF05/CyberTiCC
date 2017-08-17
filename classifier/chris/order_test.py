import json
import re
from collections import Counter
import numpy as np
import itertools
import numpy
import operator

class Tripleorder(object):
    def __init__(self, freq_dict, beam):
        self.freq_dict = freq_dict
        self.beam = beam

    def order(self, instance):
        # newinstancelist = []
        # for i in instance:
        #     newtriple = i.split(' | ')
        #     newinstancelist.append(newtriple[1])
        #
        # self.newinstance = newinstancelist
        # self.instance = instance

        sortedlist = []
        # First make a new list containing the labels for every instance of the testset with the position and occurrence information
        instancelist = []
        for label in self.newinstance:
            if label in self.freq_dict:
                instancelist.append({label: self.freq_dict[label]})
            else:
                instancelist.append({label: self.freq_dict['misc']})

        # First get an inventory of the number of times a label has appeared in an instance in the testset
        timeslist = []
        for label in instancelist:
            valuelist = list(label.values())[0]
            for value in valuelist:
                timesvalue = re.search(r'^(\d)x$', str(value))
                if timesvalue:
                    times = int(timesvalue.group(1))
                    if times not in timeslist:
                        timeslist.append(times)

        # Get all possible combinations (the Cartesian product), where repeat is possible
        combinations = [p for p in itertools.product(timeslist, repeat=len(instancelist))]
        totalcombinationlist = []
        totalproblist = []

        # For every possible combination
        for combination in combinations:
            combinationtimes = []
            combinationprobs = []
            combinationlist = []
            # Check if there is a case in the test set where the label was used the number of times
            for idx, label in enumerate(instancelist):
                key = list(label.keys())[0]
                try:
                    prob = label[key][str(combination[idx]) + 'x']
                    combinationtimes.append(combination[idx])
                    combinationprobs.append(prob)
                except KeyError:
                    break
            # If not, we will view it as an invalid combination
            if len(combinationtimes) == len(instancelist):
                # Make a list where all the instances are represented multiple times according to the combination possiblity
                # e.g.  instancelist = [{'Hoi': {1: 0.5, 2: 0.3, 3: 0.25, 4: 0.6}}, {'Hoi': {1: 0.5, 2: 0.3, 3: 0.25, 4: 0.6}},
                # {'Doei': {1: 0.3, 2: 0.6, 3: 0.15, 4: 0.2}}, {'Dag': {1: 0.3, 2: 0.7, 3: 0.5, 4: 0.3}}]
                for idx, value in enumerate(combinationtimes):
                    combinationlist += value * [instancelist[idx]]
                totalcombinationlist.append(combinationlist)
                totalproblist.append(sum(combinationprobs))

        # Sort the list containing the combinations by their probability (from highest to lowest)
        totalcombinationlist = numpy.array(totalcombinationlist)
        totalproblist = numpy.array(totalproblist)
        inds = totalproblist.argsort()
        totalcombinationlist = list(totalcombinationlist[inds])
        totalcombinationlist.reverse()

        totalsortedproblist = []

        # Now we will look at the order of the possible combinations
        for combination in totalcombinationlist:
            probdict = {}
            # Get all the possible permutations given the instances
            permutations = list(itertools.permutations(combination))

            # Now let's get the sum of probability scores for every order
            # Loop every order
            for order in permutations:
                keyorder = []
                probsum = 0
                # And every label in the order
                for idx, val in enumerate(order):
                    # Get the corresponding probability score for the position in the order
                    idx2 = idx + 1
                    key = list(val.keys())[0]
                    try:
                        prob = val[key][idx2]
                    except KeyError:
                        prob = 0
                    keyorder.append(key)
                    probsum += prob
                # And get a tuple of the order and sum of probability scores
                probdict.update({tuple(keyorder): probsum})

            # Sort the orders from highest probability to lowest
            sortedprobdict = sorted(probdict.items(), key=operator.itemgetter(1))
            sortedprobdict.reverse()
            sortedprobdict = [x[0] for x in sortedprobdict]
            totalsortedproblist.extend(sortedprobdict)
        sortedlist.append(totalsortedproblist)

        fullsortedlist = []
        # Sortedlist has the form of [[(most probable order instance 1), (second most probable order instance 1), ...], [(most probable order instance 2), (second most probable order instance 2), ...]...]
        #Find the corresponding full triple for each label in the sentence
        for sentence in sortedlist:
            sentencelist = []
            for combination in sentence:
                t = ()
                for label in combination:
                    t = t + (self.instance[self.newinstance.index(label)],)
                sentencelist.append(t)
            fullsortedlist.append(sentencelist)

        return fullsortedlist[0][:self.beam]

with open('../data/train_order.json') as json_data:
    d = json.load(json_data)
_in = d[0]['triples']
print _in

with open('../data/freq_order.json') as json_data:
    d = json.load(json_data)

test = Tripleorder(d, 4)
r = test.order(_in)

for triples in r:
    print triples