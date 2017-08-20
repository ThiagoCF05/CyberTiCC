__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 19/05/2017
Description:
    Tokenize and lowercasing the output from the systems for automatic evaluation
"""
import sys
sys.path.append('../')
import os
import xml.etree.ElementTree as ET

from db.model import *
sys.path.append('/home/tcastrof/workspace/stanford_corenlp_pywrapper')
from stanford_corenlp_pywrapper import CoreNLP
import utils

class Postprocessing(object):
    def __init__(self, fdev, ftest):
        self.proc = CoreNLP('ssplit')

        self.get_results(fdev, ftest)

        # DEV
        dev_order, dev_gold = [], []
        DEV_DIR = u'../data/dev'
        for dir in os.listdir(DEV_DIR):
            if dir != u'.DS_Store':
                f = os.path.join(DEV_DIR, dir)
                for fname in os.listdir(f):
                    if fname != u'.DS_Store':
                        _order, _gold = self.order(os.path.join(f, fname), u'dev')
                        dev_order.extend(_order)
                        dev_gold.extend(_gold)
        self.write_hyps(dev_order, fdev + '.ordered')

        utils.write_references('results/gold/dev.en', dev_gold)

        # TEST
        test_order, test_gold = [], []
        TEST_FILE = u'../data/test/triples/test.xml'
        _order, _gold = self.order(TEST_FILE, u'test')
        test_order.extend(_order)
        self.write_hyps(dev_order, ftest + '.ordered')

        # save previous orders
        self.save_prev_order()

    def save_prev_order(self):
        f = open('results/dev_prev_order.txt', 'w')
        for prev in self.dev_key_order:
            f.write('\t'.join(map(lambda x: str(x), prev)))
            f.write('\n')
        f.close()

        f = open('results/test_prev_order.txt', 'w')
        for prev in self.test_key_order:
            f.write(prev)
            f.write('\n')
        f.close()

    def get_results(self, fdev, ftest):
        def read_file(fname):
            f = open(fname)
            doc = f.read()
            f.close()

            return doc.split('\n')

        # development set
        _set = u'dev'
        entries = Entry.objects(set=_set)

        devresults = read_file(fdev)

        self.dev_order, self.dev_key_order = {}, []
        self.dev_gold = {}
        for i, entry in enumerate(entries):
            semcategory = entry.category
            size = entry.size
            docid = entry.docid
            self.dev_order[(docid, size, semcategory, _set)] = devresults[i]
            self.dev_key_order.append([docid, size, semcategory, _set])

            texts = map(lambda x: x.text, entry.texts)
            self.dev_gold[(docid, size, semcategory, _set)] = texts

        # test set
        _set = u'test'
        entries = Entry.objects(set=_set)

        testresults = read_file(ftest)

        self.test_order, self.test_key_order = {}, []
        for i, entry in enumerate(entries):
            docid= entry.docid
            self.test_order[docid] = testresults[i]
            self.test_key_order.append(docid)

    def order(self, fname, _set):
        tree = ET.parse(fname)
        root = tree.getroot()

        entries = root.find('entries')

        order = []
        gold = []

        for _entry in entries:
            docid = _entry.attrib['eid']
            size = int(_entry.attrib['size'])
            semcategory = _entry.attrib['category']

            if _set == 'dev':
                order.append(self.dev_order[(docid, size, semcategory, _set)])
                gold.append(self.dev_gold[(docid, size, semcategory, _set)])
            else:
                order.append(self.test_order[docid])
        return order, gold

    def write_hyps(self, order, fname):
        f = open(fname, 'w')
        for text in order:
            out = self.proc.parse_doc(text)
            text = ''
            for snt in out['sentences']:
                text += ' '.join(snt['tokens']).replace('-LRB-', '(').replace('-RRB-', ')')
                text += ' '

            f.write(text.encode('utf-8'))
            f.write('\n')
        f.close()


if __name__ == '__main__':
    postprocessing = Postprocessing('results/smt_dev.out', 'results/smt_test.out')
    postprocessing = Postprocessing('results/nmt_dev.out', 'results/nmt_test.out')