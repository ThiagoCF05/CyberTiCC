__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 19/05/2017
Description:
    Tokenize and lowercasing the output from the systems for automatic evaluation
"""
# encoding=utf8
import argparse
import sys

reload(sys)
sys.setdefaultencoding('utf8')
import nltk
import os

def tokenize(fread, fwrite, useNLTK=False):
    f = open(fread)
    texts = f.read().split('\n')
    f.close()

    f = open(fwrite, 'w')
    for text in texts:
        if useNLTK:
            tokens = nltk.word_tokenize(text)
        else:
            tokens = text.split()
        tokens = u' '.join(tokens)

        f.write(tokens)
        f.write('\n')
    f.close()

if __name__ == '__main__':
    # python tokenizer.py /home/tcastrof/cyber/data/easy_nlg --nltk

    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=str, default='/home/tcastrof/cyber/data/easy_nlg', help='directory')
    parser.add_argument('--fread', type=str, default='', help='file to read')
    parser.add_argument('--fwrite', type=str, default='', help='file to write')
    parser.add_argument("--nltk", action="store_true", help="NLTK tokenizer")
    args = parser.parse_args()

    if args.fread == '' and args.fwrite == '':
        print 'Hypothesis'
        fread = os.path.join(args.directory, 'hyps')
        fwrite = os.path.join(args.directory, 'hyps_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 1'
        fread = os.path.join(args.directory, 'ref1')
        fwrite = os.path.join(args.directory, 'ref1_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 2'
        fread = os.path.join(args.directory, 'ref2')
        fwrite = os.path.join(args.directory, 'ref2_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 3'
        fread = os.path.join(args.directory, 'ref3')
        fwrite = os.path.join(args.directory, 'ref3_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 4'
        fread = os.path.join(args.directory, 'ref4')
        fwrite = os.path.join(args.directory, 'ref4_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 5'
        fread = os.path.join(args.directory, 'ref5')
        fwrite = os.path.join(args.directory, 'ref5_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 6'
        fread = os.path.join(args.directory, 'ref6')
        fwrite = os.path.join(args.directory, 'ref6_tok')
        tokenize(fread, fwrite, args.nltk)

        print 'Reference 7'
        fread = os.path.join(args.directory, 'ref7')
        fwrite = os.path.join(args.directory, 'ref7_tok')
        tokenize(fread, fwrite, args.nltk)
    else:
        fread = args.fread
        fwrite = args.fwrite
        tokenize(fread, fwrite, args.nltk)