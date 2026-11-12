# Data

All article text comes from Wikipedia, Simple English Wikipedia and Vikidia (CC BY-SA), collected through the MediaWiki API by `python -m lingualadder.collect`.

The project uses English and Spanish:

| File | What it is | Articles |
|---|---|---|
| `raw/enwiki.jsonl` | Regular English Wikipedia articles on 50 seed topics | part of 992 en |
| `raw/simplewiki.jsonl` | Simple English Wikipedia (the "easy" label for English) | |
| `raw/enwiki_random.jsonl` | Random English articles (background vocabulary) | |
| `raw/eswiki.jsonl` | Regular Spanish Wikipedia articles on the same topics | part of 756 es |
| `raw/esvikidia.jsonl` | Vikidia, the children's encyclopedia (the "easy" label for Spanish) | |
| `raw/eswiki_random.jsonl` | Random Spanish articles | |

Each line is one JSON object: `pageid`, `title`, `url`, `text`, `topic` (the seed topic it was collected for), `en_title`, `source`, `lang`, `easy` (1 for Simple English or Vikidia, 0 otherwise).



Generated files (not in the repo, rebuilt by `python -m lingualadder.build`): `index.pkl` (BM25 indexes + difficulty scores), `corpus.jsonl`, `models/`.

Experiment outputs: `eval_report.md`, `eval_results.json`, `grad_eval.json` (significance tests), `difficulty_exp.json`, `adapt_eval.json`, `adapt_sweep.json`.
