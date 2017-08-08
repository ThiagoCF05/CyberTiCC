#!/bin/bash

# no references
rm -R /home/tcastrof/cyber/data/nmt/delex/
mkdir /home/tcastrof/cyber/data/nmt/delex/

python parallel_data.py /home/tcastrof/cyber/data/nmt/delex/train.de /home/tcastrof/cyber/data/nmt/delex/train.en 10 --delex

python parallel_data.py /home/tcastrof/cyber/data/nmt/delex/dev.de /home/tcastrof/cyber/data/nmt/delex/dev.en 10 --dev --delex

mkdir /home/tcastrof/cyber/data/nmt/delex/refs
python parallel_data.py /home/tcastrof/cyber/data/nmt/delex/refs/dev.de_gold /home/tcastrof/cyber/data/nmt/delex/refs/dev.ref 10 --dev --eval --delex