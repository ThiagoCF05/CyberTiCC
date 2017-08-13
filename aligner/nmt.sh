#!/bin/bash

# no references
rm -R /home/tcastrof/cyber/data/nmt/delex/
mkdir /home/tcastrof/cyber/data/nmt/delex/

python parallel_data.py /home/tcastrof/cyber/data/nmt/delex/train 10 --delex

python parallel_data.py /home/tcastrof/cyber/data/nmt/delex/dev 10 --dev --delex

mkdir /home/tcastrof/cyber/data/nmt/delex/refs
python parallel_data.py /home/tcastrof/cyber/data/nmt/delex/refs/eval1 10 --dev --eval --delex

# references
rm -R /home/tcastrof/cyber/data/nmt/lex/
mkdir /home/tcastrof/cyber/data/nmt/lex/

python parallel_data.py /home/tcastrof/cyber/data/nmt/lex/train 10

python parallel_data.py /home/tcastrof/cyber/data/nmt/lex/dev 10 --dev

mkdir /home/tcastrof/cyber/data/nmt/lex/refs
python parallel_data.py /home/tcastrof/cyber/data/nmt/lex/refs/eval1 10 --dev --eval