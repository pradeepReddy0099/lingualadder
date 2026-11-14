# LinguaLadder

**Wikipedia search ranked for relevance *and* reading level, for learners of English and Spanish.**

Graduate Information Retrieval course project by Pradeep Reddy Sama, Marco Cerritos, Akshay Karasani and Ryan Zappone.

- **Project site (questions, takeaways, results):** https://pradeepreddy0099.github.io/lingualadder/
- **Live demo (runs in the browser, no install):** https://pradeepreddy0099.github.io/lingualadder/app/
- **Data:** included in [`data/raw/`](data/raw/) (see [`data/README.md`](data/README.md))

## Set up and run

Requires **Python 3.10+** and an internet connection only for highlight-to-translate.

```bash
git clone https://github.com/pradeepReddy0099/lingualadder.git
cd lingualadder
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m lingualadder.build      # trains the difficulty model, builds BM25 indexes from data/raw (~15 s)
python app.py                     # open http://127.0.0.1:5000
```

Or run `./run.sh` (install, build, evaluate, start the app).

**Dependencies** (`requirements.txt`): flask, requests, regex, numpy, scikit-learn, scipy, snowballstemmer, pytest.
No API key is needed. Translation uses the free Google Translate endpoint with MyMemory as a fallback; set
`GOOGLE_API_KEY` to use Google Cloud Translation instead.

**Reproduce the results**

```bash
python -m lingualadder.evaluate      # difficulty model + retrieval tables -> data/eval_report.md
python -m lingualadder.grad_eval     # baselines, ablations, significance tests -> data/grad_eval.json
python -m lingualadder.adapt_eval    # adaptive-level simulation -> data/adapt_eval.json
pytest                               # unit tests
```

**Browser version:** `python -m lingualadder.export_web` writes `web/data/{en,es}.json`; then serve `web/`
(`python -m http.server -d web`). `node web/parity_test.js` checks that the JavaScript ranking matches Python.
The copy in `docs/app/` is what GitHub Pages serves.

## Data

17,208 articles collected from Wikipedia through the MediaWiki API on 304 topics (volcanoes, football, chocolate,
Frida Kahlo, chess, ...): **8,408 English** (2,114 easy) and **8,800 Spanish** (2,086 easy). The easy examples come from Simple English Wikipedia
and Vikidia; the regular ones from English and Spanish Wikipedia. The raw JSONL files are in `data/raw/`; re-collect
with `python -m lingualadder.collect` (~15 minutes). Text is CC BY-SA.

## How it works

```
query ─► BM25 over the language's index (top 100 candidates)
      ─► re-rank:  score = a · BM25/max  +  (1 − a) · exp(−(difficulty − target)² / 2σ²)     a = 0.5, σ = 0.15
      ─► top 10 with level + CEFR badges ─► reader with highlight-to-translate
      ─► "too easy / too hard" feedback moves the learner's target level
```

| Module | What it does |
|---|---|
| `lingualadder/collect.py` | Downloads topical articles from Wikipedia, Simple English Wikipedia and Vikidia |
| `lingualadder/textproc.py` | Tokenization and the 15 difficulty features |
| `lingualadder/difficulty.py` | Logistic regression difficulty model (features z-scored per language) |
| `lingualadder/search.py` | BM25 written from scratch, level-aware re-ranker, adaptive target |
| `lingualadder/translate.py` | Highlight-to-translate with a SQLite cache |
| `lingualadder/evaluate.py`, `grad_eval.py`, `adapt_eval.py` | Experiments |
| `app.py`, `templates/`, `static/` | Flask app: profile, search, BM25 side-by-side, reader, word list |
| `web/` | Static in-browser version (JS BM25 + re-ranker) |

Levels: Beginner < 0.35 ≤ Intermediate < 0.65 ≤ Advanced, targets 0.20 / 0.50 / 0.80.

## Results (English + Spanish: 152 English and 179 Spanish queries, each at 3 levels)

Corpus: 8,408 English articles (2,114 easy) and 8,800 Spanish articles (2,086 easy). Every one of the 304 topics has
at least one beginner, one intermediate and one advanced article in both languages. Top 10 results, default settings
(topic guard on, a = 0.5).

| Language | System | P@10 | nDCG@10 | Level match (±0.15 of target) |
|---|---|---|---|---|
| English | Plain BM25 | 0.801 | 0.819 | 0.218 |
| English | **LinguaLadder** | 0.725 | 0.734 | 0.493 |
| Spanish | Plain BM25 | 0.731 | 0.764 | 0.226 |
| Spanish | **LinguaLadder** | 0.666 | 0.683 | 0.427 |
| Both | Plain BM25 | 0.766 | 0.792 | 0.222 |
| Both | **LinguaLadder** | 0.695 | 0.709 | 0.460 |

- Level match roughly doubles for a cost of about 0.08 nDCG@10. The weight `a` moves along this trade-off
  (alpha sweep in `data/eval_report.md`: a = 0.8 gives nDCG@10 0.781 and level match 0.350).
- Difficulty model: 0.860 accuracy (5-fold CV) vs 0.772 for sentence and word length alone; trained on one language
  and tested on the other it reaches 0.804 (es) and 0.879 (en).
- Second evaluation (`data/grad_eval.json`, 331 queries, source-label level fit with paired significance tests):
  level fit by source label 0.500 (BM25) -> 0.762 (LinguaLadder). It uses a different relevance judgement, so its
  nDCG@10 values (0.789 -> 0.507) are not comparable with the table above.
- Adaptive level: in simulation, "too easy / too hard" feedback cut the gap to a learner's ideal difficulty from
  0.264 to 0.136.
- Relevance labels are automatic (an article is relevant if it was collected for the query's topic), so true
  precision is probably higher.

## Limitations

Automatic relevance labels; level match judged with our own difficulty scores (we also report a source-label
measure); simulated rather than real learners; easy articles are still fewer than regular ones on many topics.
