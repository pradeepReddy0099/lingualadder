# Changelog

## Static web version: index export, JS search core, first page (W1, W2)
- `python -m lingualadder.export_web [langs]` writes `web/data/<lang>.json`: documents (title, url, snippet, difficulty, level), doc lengths and delta-coded BM25 postings with idf, plus stop words and the ranking constants. All five languages: en 3.9 MB, es 2.7, fr 3.0, hi 1.0, ja 5.3 (15.9 MB raw, about 4.6 MB gzipped; the page loads one language at a time).
- `web/ll.js` ports the tokenizer (including CJK bigrams), BM25 and the level-fit reranker. `python -m lingualadder.web_parity` writes Python's top-10 for 27 query/level cases (en, es, fr, hi, ja); `node web/parity_test.js` reproduces all 27 rankings exactly (max score difference 7e-5, from rounding idf to 3 decimals).
- `web/index.html`, `app.js`, `style.css`: search box, language and level pickers, level badges, relevance and fit bars, plain-BM25 toggle. Serve with `python -m http.server --directory web`.

## 2026-11-11: Better difficulty model (extended features)
- Added 7 language-independent features on top of the original 8 (`textproc.ext_features`): syllables per word (kanji density for Japanese, vowel signs for Hindi), CEFRLex-style frequency bands (share of words in the language's top-500 core vocabulary and in the 500-3000 band), subordinate-clause markers per sentence, commas per sentence, sentence-length spread, share of long sentences.
- New experiment script `python -m lingualadder.difficulty_exp` (results in data/difficulty_exp.json) comparing LR, stronger-regularized LR and gradient boosting on base vs extended features:

| Features | Model | CV acc | CV AUC | Unseen-language acc (mean) |
|---|---|---|---|---|
| base 8 | LR (before) | 0.849 | 0.890 | 0.844 |
| base 8 | Gradient boosting | 0.853 | 0.893 | 0.832 |
| extended 15 | LR (adopted) | **0.865** | 0.901 | 0.848 |
| extended 15 | LR C=0.1 | 0.860 | 0.901 | 0.851 |
| extended 15 | Gradient boosting | 0.859 | 0.906 | 0.843 |

- Kept logistic regression: boosting fit slightly better in-language but transferred worse to an unseen language, which matters for Hindi/Japanese.
- Retrieval (grad_eval, labeled languages, LinguaLadder vs the same system with the old 8-feature model): nDCG@10 0.772 -> 0.771 (no significant change), source-label level fit 0.623 -> 0.632 (perm p = 0.025). evaluate.py summary: P@10 0.635 -> 0.631, nDCG@10 0.743 -> 0.737. Level match from evaluate.py (0.403 -> 0.395) is judged with each model's own difficulty scores, so it is not comparable across models; see new roadmap item.
- grad_eval gains an `LL-8feat` system (old feature set) and the rarity ablation now drops all frequency-band features. scipy added to requirements.

## Fusion sweep (no default change)
Swept alpha {0.5,0.6,0.7} x sigma {0.15,0.25} x relevance floor {0,0.3,0.4,0.5,0.6}, scoring harmonic mean of nDCG@10 and level match.
Default (0.5, 0.15, no floor) stays best: nDCG 0.737, level match 0.395, harmonic 0.514. Best floor variant: 0.486 (nDCG 0.768, level 0.356). Added optional `min_rel` to search/evaluate.

## Difficulty calibration experiment (off by default)
Percentile-ranking difficulty per language so targets 0.2/0.5/0.8 hold equal corpus shares (opt-in via LL_CALIBRATE=1).
grad_eval labeled: nDCG@10 0.771 -> 0.728, P@10 0.718 -> 0.646, source-label level fit (gold_level) 0.632 -> 0.663. Gain in level fit costs more relevance than it is worth at alpha 0.5, so it stays off. Idea: pair with a higher alpha.

## Smoke tests
- Added pytest smoke tests for home and search (tests/test_app.py); 2 pass. No ranking change.

## Web: explicit "Read full article on Wikipedia" link per result (UI only, no ranking change)

## Tests: textproc
Added tests/test_textproc.py (5 tests); suite 7 passing. No ranking change.

## Web: ja index shrink
- Dropped df=1 terms for CJK in export_web: ja.json 5.32 MB -> 4.11 MB; JS/Python parity 27/27 still matches.

## Tests: BM25 and reranker
Added tests/test_search.py (3 tests); suite 10 passing. No ranking change.

## Web: mobile layout
- Added narrow-screen CSS (full-width 44px controls) and visible focus outlines. No ranking change.

## ALPHA x SIGMA grid sweep (no default change)
Harmonic mean of nDCG@10 and level match, LL reranker: a=0.5/s=0.15: 0.514 (P@10 0.631, nDCG 0.737, LM 0.395); a=0.5/s=0.10: 0.516; a=0.6/s=0.10: 0.485; a=0.7/s=0.10: 0.452. Higher alpha buys relevance (a=0.7: nDCG 0.829) at the cost of level match (0.311). Defaults kept; use alpha 0.6-0.7 as a "relevance-first" option.

## Input validation
Profile form now rejects unsupported language/level with HTTP 400 (was a 500/KeyError). No ranking change; metrics unchanged.

## Adaptive target helper
- Added search.adapt_target(target, feedback) (+0.05 per too_easy, -0.05 per too_hard, clamped) with a unit test. No ranking change, so metrics unchanged.

## Web: side-by-side compare
Added 'Side-by-side compare' toggle (plain BM25 vs LinguaLadder columns). JS parity test unchanged.

## Feedback wiring
- /api/feedback now uses search.adapt_target (clamped offset, 400 on invalid verdict). Behaviour unchanged for valid input; no ranking metrics affected.

## Web: reader view
Added large-text Reader view toggle (W3 done). No ranking change; metrics unchanged.

## CEFR helper
Added cefr_label (difficulty -> A1-C2, uncalibrated) with a test. No ranking change; metrics unchanged.

## CEFR band in web UI
Web result cards now show an approximate CEFR band (A1-C2) next to the level badge, same cutoffs as cefr_label. No ranking change, so no metric change.

## Fixed reference judge
Marked done: gold_level in grad_eval already judges level fit from source labels, independent of the difficulty model. No ranking change; metrics unchanged.

## Web: CEFR band summary
- Status line now shows CEFR band counts of the results. No metric change (UI only).

## CEFR band in Flask UI
Results and reader now show an approximate CEFR band next to difficulty. Display only; no metric change (rankings untouched). 12 tests pass.

## Accessibility pass (web)
- Status line announces updates (aria-live); language and level selects labelled. No metric change.

## CEFR band calibration
Band cutoffs now use corpus quantiles (10/25/45/65/85%) instead of even steps. Before: 58% of documents landed in C2 (C2 1851, C1 436, B2 223, B1 179, A2 210, A1 269 of 3168). After: A1 308, A2 486, B1 656, B2 557, C1 624, C2 537. Display only, rankings untouched; 12 tests and 27/27 JS parity pass.

## Size check
Web bundle verified under the 15 MB target (about 15 MB on disk, 27/27 parity checks pass, 12 tests pass). No metric change.

## Vocab-aware rerank (opt-in)
- search() accepts known words and beta; boosts snippets mostly of known words. Default off, so no metric change (P@10 0.745 BM25 / LL 0.631 unchanged). Test added; 13 tests pass.

## Single-file web build
Added build_single: inlines CSS, JS and chosen language indexes into one HTML file (Hindi build 0.75 MB) because Hark Pages hold one file. Ranking untouched; no metric change. 13 tests and 27/27 JS parity pass.

## Snowball stemming (opt-in)
LL_STEM=1 stems en/es/fr tokens. BM25 P@10 0.745 -> 0.756, nDCG 0.877 -> 0.886; LinguaLadder P@10 0.631 -> 0.612, nDCG 0.737 -> 0.714, level match 0.395 -> 0.432. Mixed, so off by default.

## Scope: English and Spanish only
- French, Hindi and Japanese dropped from the supported language list, the web bundle (6.3 MB raw, down from 15 MB), the web dropdown and the eval harnesses. Their raw data is still on disk.
- New en+es baseline (NOT comparable to the earlier five-language numbers): difficulty CV accuracy 0.888 (F1 0.929). Retrieval: BM25 P@10 0.865, nDCG@10 0.920, level match 0.162; LinguaLadder P@10 0.730, nDCG@10 0.771, level match 0.359. Source-label level fit (gold_level): BM25 0.500, LinguaLadder 0.646.
- Web parity test: 15/15 match; pytest 13 passed.

## Stemming re-measured on en+es
LL_STEM=1 on the en+es baseline: BM25 P@10 0.865 -> 0.884, nDCG@10 0.920 -> 0.936 (better); LinguaLadder P@10 0.730 -> 0.697, nDCG@10 0.771 -> 0.735 (worse), level match 0.359 -> 0.407 (better). Mixed, so stemming stays opt-in. No default change; 13 tests pass.

## Published web version
- Built the single-file en+es web app (6.5 MB) and published it as the Hark Page "LinguaLadder". Parity with Python: 15/15 queries match. No ranking change, so no metric change.

## Adaptive target, offline simulation
- New adapt_eval simulates learners with a hidden ideal difficulty (low or high) starting from three targets, giving too-easy/too-hard feedback on the top result over 18 queries (en+es). Mean gap between result difficulty and the ideal: fixed target 0.264, adaptive 0.136 (smaller is better). Gains are largest when the starting level is wrong; with a well-matched start it is about equal. Simulated, not real users. Ranking default unchanged; 13 tests pass.

## Web: remembered profile and shareable links
- The web app remembers language and level between visits and opens a search from a ?q= link. Ranking untouched; no metric change. Parity and 13 tests pass.

## Adaptive target: step and tolerance sweep
Mean gap between result difficulty and the simulated learner's ideal (lower is better), 12 scenarios, fixed target gap 0.264:
step 0.03: 0.177-0.190; 0.05: 0.146-0.155; 0.07 (current): 0.136-0.143; 0.10: 0.123-0.132; 0.15: 0.118-0.122. Tolerance matters little (0.05-0.1 equal, 0.15 slightly worse).
Larger steps look slightly better, but the simulated learner is noiseless, so a bigger step would likely overreact to real, noisy clicks; default step stays 0.07. No ranking metric change.

## Web: search shortcut and empty state
- Pressing "/" focuses the search box, Escape clears it, and a query with no matches now shows a friendly message. Ranking untouched; no metric change. Parity and 13 tests pass.

## Adaptive target: noisy learner and step decay
Mean gap to the simulated ideal (lower is better), with 30% of feedback replaced by random answers: step 0.07 no decay 0.136 (clean) / 0.153 (noisy); step 0.07 with decay 0.95: 0.144 / 0.162 (worse); step 0.15 no decay 0.122 / 0.136; step 0.15 decay 0.9: 0.117 / 0.133 (best). Decay hurts at the small step and helps slightly at the large one. A larger step stays better even under noise, so a step near 0.10-0.15 is worth testing in the UI; default left at 0.07 for now. No ranking change.

## Corpus collection progress
English 5,500 articles cached; Spanish 3,620 of 5,500 cached. Collector resumes next run.

## 2026-11-12 — Topic guard (fit algorithm, user request)
- Problem (user report): searches returned articles that merely contain the word, not articles about the topic (e.g. "dog" → "Soda bread"), because level fit could lift low-relevance passing mentions.
- Change: idf-weighted topicality = query words in the title (full) or opening lead (half). Relevance = 0.6·BM25/max + 0.4·topicality; articles below 0.5 topicality rank after all on-topic ones. Same in Python and the browser (15/15 parity). Plain BM25 baseline unchanged. Demo marks passing mentions with a "mentions" badge and says when nothing is mainly about the query.
- Before → after (LinguaLadder, en+es, 94 queries × 3 levels): P@10 0.730 → 0.852, nDCG@10 0.771 → 0.898, level match 0.359 → 0.201. Default on (TOPIC_WEIGHT=0.4, ON_TOPIC_MIN=0.5). The level-match drop reflects few on-topic articles per level in the 1,748-article corpus; re-test after the 5,000-per-language corpus.
- Tests: 14 passed (new on-topic test); parity 15/15; app smoke test OK.

## 2026-11-12 — Redesign, placement test, recommendations (website, user request)
- New interface: gradient header, search card with a big search bar, level picker, display options as switches, colored level stripes and CEFR pills, dark mode, mobile layout.
- Placement test ("Find my level"): 24-item vocabulary yes/no check (18 real words from six corpus-frequency bands + 6 invented pseudowords; hit rate corrected for guessing) and an 8-item adaptive cloze (fill the blank in real article openings, 4 options, staircase over difficulty quantiles). Combined 0.6·reading + 0.4·vocabulary → personal target difficulty and CEFR band; replaces self-reported level when chosen. Simulated learners (node web/placement_test.js): mean absolute error 0.119 (en) and 0.137 (es) in difficulty quantile; estimates order correctly (0.31/0.56/0.87 en for abilities 0.15/0.50/0.85). Not yet validated with real learners.
- Recommendations: topic chips ranked by articles near the learner's level (unread first); "The ladder for this topic" strip with one on-topic pick per level; "Read next ↑" per article (same topic, next step harder, unread); "Too easy / Too hard" moves the personal target by 0.07 quantile.
- Coverage tool (python -m lingualadder.coverage [--fill]): reports topics missing a level and fetches candidates to fill gaps. Current corpus: en 31/50, es 22/50 topics have all three levels (mostly missing intermediate).
- Tests: pytest 14 passed, parity 15/15, app smoke test OK, placement test 8/8.

## Spanish boost
- Merged the Spanish boost (Vikidia + Spanish Wikipedia) and rebuilt. Docs: en 8,282 (2,039 easy), es 8,109 (1,908 easy); before: en 8,159 total / 1,964 easy, es 7,419 / 1,338. Spanish easy articles grew +570 but still trail English by 131; Spanish total trails by 173.
- Levels after: en beginner 1,266 / intermediate 885 / advanced 6,131; es 1,040 / 1,020 / 6,049.
- Coverage: en 302/304 topics complete (gaps: Gabriel García Márquez beginner, Photography intermediate); es 294/304 (was 287). Fill rounds found no new candidates for the remaining 10 es topics: Inca Empire, Barcelona, Vegetable, Magnetism, Carnival, Corn (beginner); Colombia, Painting, Martial arts (intermediate); Tourism (both).
- evaluate.py overall: P@10 0.774 -> 0.707, nDCG@10 0.8 -> 0.72, level match 0.211 -> 0.441 (BM25 -> LL). en nDCG LL 0.73-0.75, es 0.69-0.71. grad_eval summary unchanged (nDCG 0.516, gold level fit 0.757).
- Web data: en 21.8 MB + two parts (5.2 MB), es 23.2 MB; 45 MB total. Parity 14/15 (one 5e-5 score tie in en), smoke and placement tests pass, pytest 14 pass.
- Next: another easy Spanish source (e.g. Spanish children's encyclopedias) and targeted fill for the 12 gap topics.

## Spanish boost
- Vikidia/Spanish Wikipedia boost merged. Spanish now 8,109 docs (1,908 easy) vs English 8,282 (before: es 7,419 total / 1,338 easy). Levels es: beginner 1,040, intermediate 1,020, advanced 6,049; en: 1,266 / 885 / 6,131.
- Coverage: en 302/304 topics, es 294/304 (before 299 / 287); extra fill found no new candidates for the remaining gaps.
- Overall eval: BM25 P@10 0.774, nDCG 0.800; LinguaLadder P@10 0.707, nDCG 0.720, level match 0.441.
- Web data re-exported: en 26.98 MB (3 parts), es 23.18 MB.

## Flask parity: Too easy / Too hard buttons
- Search results in the Flask app now have Too easy and Too hard buttons that call the feedback endpoint and step the target level. No ranking change (metrics unchanged). Tests: 14 pass; /search returns 200 for en and es.

## Flask error pages
- Added friendly 404 and 500 pages with a link home, plus a test. No ranking change (metrics unchanged). Tests: 15 pass; /search?q=volcano returns 200.

## Spanish Flask test
- Added a Spanish search test for the Flask app. No ranking change. Tests: 16 pass.

## Feedback test (en and es)
- Added a test that too hard / too easy feedback moves the target level in English and Spanish and rejects bad verdicts. No ranking change. Tests: 17 pass.

## Coverage report test
- Added a test that the en and es coverage reports are consistent (complete + gaps = 304 topics, at least 290 complete). No ranking change. Tests: 18 pass.

## Coverage closed: every topic, every level, both languages
- New `python -m lingualadder.coverage_extra`: hand-picked related search terms per stubborn topic (e.g. Inca Empire -> Machu Picchu, Tahuantinsuyo; Martial arts -> Judo, Capoeira), fetched from Vikidia / Simple English and short regular articles. Because difficulty is z-scored within a language, each rebuild shifts levels slightly, so it was run in rounds (four builds) until both languages were complete.
- Coverage: en 302/304 -> 304/304 topics with beginner, intermediate and advanced; es 294/304 -> 304/304.
- Corpus: en 8,282 -> 8,408 docs (2,039 -> 2,114 easy); es 8,109 -> 8,800 docs (1,908 -> 2,086 easy). Spanish now has more articles than English (+392) and trails English by 28 easy articles.
- Levels (beginner / intermediate / advanced): en 1,266 / 885 / 6,131 -> 1,264 / 947 / 6,197; es 1,040 / 1,020 / 6,049 -> 1,114 / 1,174 / 6,512.
- evaluate.py, English and Spanish separately (nDCG@10 BM25 -> LinguaLadder, averaged over levels): en 0.819 -> 0.734, es 0.764 -> 0.683; level match en 0.218 -> 0.493, es 0.226 -> 0.427. Overall P@10 0.774 -> 0.766 (BM25), 0.707 -> 0.695 (LL); nDCG@10 0.800 -> 0.792 (BM25), 0.720 -> 0.709 (LL); level match 0.441 -> 0.460 (LL). grad_eval: LinguaLadder gold level fit 0.757 -> 0.762, nDCG@10 0.516 -> 0.507.
- Web data re-exported: en 27.1 MB (3 parts), es 24.0 MB (3 parts), 41.3 MB total (was 45 MB).
- README and docs/index.html now show these numbers (they still had the old 1,748-article results). Tests: pytest 18 pass; parity 15/15; app smoke, placement tests pass; /search?q=volcano 200 (en) and es 200.
- Next: remaining easy-article gap in Spanish (28), then Better fit algorithm items.
