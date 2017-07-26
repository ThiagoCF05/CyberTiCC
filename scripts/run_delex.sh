#!/bin/bash

cd db/
python init.py

cd ../delexicalizer
python manual.py
python delex.py

cd ../classifier
python ordering.py
python maxent.py

cd ../scripts
python report.py