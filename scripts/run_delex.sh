#!/bin/bash

cd db/
python init.py

cd ../delexicalizer
python delex.py

cd ../classifier
python ordering.py

cd ../scripts
python report.py