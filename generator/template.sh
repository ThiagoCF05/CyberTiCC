#!/bin/bash

python reg/reg_train.py
mv data.cPickle reg/

rm -R /home/tcastrof/cyber/data/template/manual
mkdir /home/tcastrof/cyber/data/template/manual

python cybernlg.py \
	/home/tcastrof/cyber/data/template/manual/dev \
	/home/tcastrof/cyber/data/template/manual/ref \
	/home/tcastrof/cyber/data/template/manual/test \
	manual

rm -R /home/tcastrof/cyber/data/template/automatic
mkdir /home/tcastrof/cyber/data/template/automatic

python cybernlg.py \
	/home/tcastrof/cyber/data/template/automatic/dev \
	/home/tcastrof/cyber/data/template/automatic/ref \
	/home/tcastrof/cyber/data/template/automatic/test \
	 automatic+manual