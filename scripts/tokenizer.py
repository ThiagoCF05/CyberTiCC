__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 19/05/2017
Description:
    Tokenize the output from the systems for automatic evaluation
"""

import nltk

def tokenize(fread, fwrite):
    f = open(fread)
    texts = f.read().split('\n')
    f.close()

    f = open(fwrite, 'w')
    for text in texts:
        tokens = ' '.join(nltk.word_tokenize(text))
        f.write(tokens.encode('utf-8'))
        f.write('\n')
    f.close()

if __name__ == '__main__':
    print 'Hypothesis'
    fread = '/home/tcastrof/cyber/data/easy_nlg/hyps'
    fwrite = '/home/tcastrof/cyber/data/easy_nlg/hyps_tok'
    tokenize(fread, fwrite)

    print 'Reference 1'
    fread = '/home/tcastrof/cyber/data/easy_nlg/ref1'
    fwrite = '/home/tcastrof/cyber/data/easy_nlg/ref1_tok'
    tokenize(fread, fwrite)

    print 'Reference 2'
    fread = '/home/tcastrof/cyber/data/easy_nlg/ref2'
    fwrite = '/home/tcastrof/cyber/data/easy_nlg/ref2_tok'
    tokenize(fread, fwrite)

    print 'Reference 3'
    fread = '/home/tcastrof/cyber/data/easy_nlg/ref3'
    fwrite = '/home/tcastrof/cyber/data/easy_nlg/ref3_tok'
    tokenize(fread, fwrite)

    print 'Reference 4'
    fread = '/home/tcastrof/cyber/data/easy_nlg/ref4'
    fwrite = '/home/tcastrof/cyber/data/easy_nlg/ref4_tok'
    tokenize(fread, fwrite)

    print 'Reference 5'
    fread = '/home/tcastrof/cyber/data/easy_nlg/ref5'
    fwrite = '/home/tcastrof/cyber/data/easy_nlg/ref5_tok'
    tokenize(fread, fwrite)