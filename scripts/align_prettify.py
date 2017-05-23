__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 19/05/2017
Description:
    Show the relation among triples and text based on MGIZA results
"""

# encoding=utf8
import argparse
import os

def read(fname):
    f = open(fname)
    doc = map(lambda x: x.split(), f.read().split('\n'))
    f.close()
    return doc

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', type=str, default='/home/tcastrof/cyber/data/delex', help='working directory')
    args = parser.parse_args()

    DE_EN_FILE = os.path.join(args.dir, 'model/aligned.grow-diag-final')
    DE_FILE = os.path.join(args.dir, 'train.de')
    EN_FILE = os.path.join(args.dir, 'train.en')
    OUT_FILE = os.path.join(args.dir, 'align.txt')

    de = read(DE_FILE)
    en = read(EN_FILE)
    de_en = read(DE_EN_FILE)

    f = open(OUT_FILE, 'w')
    for i, e in enumerate(de):
        for j, word in enumerate(en[i]):
            f.write(word.encode('utf-8'))
            f.write('_')
            f.write(str(j).encode('utf-8'))
            f.write(' ')
        f.write('\n')

        alignments = []
        for j, word in enumerate(de[i]):
            alignments.append([word, []])

        for j, align in enumerate(de_en[i]):
            i1, i2 = map(lambda x: int(x), align.split('-'))
            alignments[i2].append(i1)

        for j, alignment in enumerate(alignments):
            f.write(alignment[0].encode('utf-8'))
            f.write('~')
            f.write(','.join(map(lambda x: str(x), sorted(list(set(alignment[1]))))))
            f.write(' ')
        f.write('\n\n')
    f.close()