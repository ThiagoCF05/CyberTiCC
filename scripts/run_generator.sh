#!/bin/bash

cd ../generator/reg
python pronoun.py
python proper_name.py

cd ../
python simplenlg.py /home/tcastrof/cyber/data/easy_nlg_reg/hyps /home/tcastrof/cyber/data/easy_nlg_reg/ref