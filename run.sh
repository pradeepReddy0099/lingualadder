#!/usr/bin/env bash
# One-command setup: install, build the index from the included data, evaluate, start the app.
set -e
pip install -r requirements.txt
[ -f data/raw/enwiki.jsonl ] || python -m lingualadder.collect   # only if raw data is missing (~15 min)
python -m lingualadder.build
python -m lingualadder.evaluate
python app.py
