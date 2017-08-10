#!/bin/bash

# no references
rm -R /home/tcastrof/cyber/data/smt/lex/
mkdir /home/tcastrof/cyber/data/smt/lex/

python parallel_data.py /home/tcastrof/cyber/data/smt/lex/train 10

python parallel_data.py /home/tcastrof/cyber/data/smt/lex/dev 10 --dev

mkdir /home/tcastrof/cyber/data/smt/lex/refs
python parallel_data.py /home/tcastrof/cyber/data/smt/lex/refs/eval 10 --dev --eval

cd /home/tcastrof/cyber/data/smt/lex

perl /home/tcastrof/workspace/mosesdecoder/scripts/training/train-model.perl \
    -root-dir . \
    --corpus train \
    -mgiza \
    --max-phrase-length 9 \
    -external-bin-dir /home/tcastrof/workspace/mgiza \
    --f de --e en \
    --parallel \
    --distortion-limit 6 \
    --lm 0:6:/roaming/tcastrof/gigaword/gigaword.bin \
    -reordering phrase-msd-bidirectional-fe,hier-mslr-bidirectional-fe

perl /home/tcastrof/workspace/mosesdecoder/scripts/training/mert-moses.pl \
        dev.de \
        dev.en \
    /home/tcastrof/workspace/mosesdecoder/bin/moses \
    model/moses.ini \
    --mertdir /home/tcastrof/workspace/mosesdecoder/mert \
    --rootdir /home/tcastrof/workspace/mosesdecoder/scripts \
    --nbest 1000 \
    --decoder-flags '-threads 25 -v 0' \
    --batch-mira --return-best-dev \
    --batch-mira-args '-J 60'

/home/tcastrof/workspace/mosesdecoder/bin/moses -f mert-work/moses.ini -s 1000 < refs/eval.de > eval.out

# references
rm -R /home/tcastrof/cyber/data/smt/lex_ref/
mkdir /home/tcastrof/cyber/data/smt/lex_ref/

python parallel_data.py /home/tcastrof/cyber/data/smt/lex_ref/train 10 --references

python parallel_data.py /home/tcastrof/cyber/data/smt/lex_ref/dev 10 --dev

mkdir /home/tcastrof/cyber/data/smt/lex_ref/refs
python parallel_data.py /home/tcastrof/cyber/data/smt/lex_ref/refs/eval 10 --dev --eval

cd /home/tcastrof/cyber/data/smt/lex_ref

perl /home/tcastrof/workspace/mosesdecoder/scripts/training/train-model.perl \
    -root-dir . \
    --corpus train \
    -mgiza \
    --max-phrase-length 9 \
    -external-bin-dir /home/tcastrof/workspace/mgiza \
    --f de --e en \
    --parallel \
    --distortion-limit 6 \
    --lm 0:6:/roaming/tcastrof/gigaword/gigaword.bin \
    -reordering phrase-msd-bidirectional-fe,hier-mslr-bidirectional-fe

perl /home/tcastrof/workspace/mosesdecoder/scripts/training/mert-moses.pl \
        dev.de \
        dev.en \
    /home/tcastrof/workspace/mosesdecoder/bin/moses \
    model/moses.ini \
    --mertdir /home/tcastrof/workspace/mosesdecoder/mert \
    --rootdir /home/tcastrof/workspace/mosesdecoder/scripts \
    --nbest 1000 \
    --decoder-flags '-threads 25 -v 0' \
    --batch-mira --return-best-dev \
    --batch-mira-args '-J 60'

/home/tcastrof/workspace/mosesdecoder/bin/moses -f mert-work/moses.ini -s 1000 < refs/eval.de > eval.out