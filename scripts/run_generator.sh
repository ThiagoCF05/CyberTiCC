#!/bin/bash

cd generator/reg
python pronoun.py
python proper_name.py

cd ../
python cybernlg.py /home/tcastrof/cyber/data/new_nlg_reg/hyps /home/tcastrof/cyber/data/new_nlg_reg/ref