#!/bin/bash

rm -R /home/tcastrof/cyber/data/template/manual
mkdir /home/tcastrof/cyber/data/template/manual

python cybernlg.py \
	/home/tcastrof/cyber/data/template/manual/hyps \
	/home/tcastrof/cyber/data/template/manual/ref \
	manual

rm -R /home/tcastrof/cyber/data/template/automatic
mkdir /home/tcastrof/cyber/data/template/automatic

python cybernlg.py \
	/home/tcastrof/cyber/data/template/automatic/hyps \
	/home/tcastrof/cyber/data/template/automatic/ref \
	 automatic+manual