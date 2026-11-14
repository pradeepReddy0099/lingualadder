# LinguaLadder improvement roadmap (worked on by hourly runs)

Each hourly run: pick the top unchecked item, do it fully, test it, commit, tick it here, log it in CHANGELOG.md.

## Better fit algorithm (top priority, user asked 2026-11-11)
Goal: results that fit the learner's level better WITHOUT losing much relevance. Baseline: BM25 P@10 0.745, nDCG@10 0.877, level match 0.219; current reranker (a=0.5) P@10 0.635, nDCG@10 0.743, level match 0.403.
- [x] Better difficulty model: try gradient boosting / calibrated LR, add features (CEFRLex-style word-frequency bands, syllables/word, subordinate-clause markers), report CV accuracy vs 0.849. (done: 15 features + LR, CV 0.865; GBT did not transfer better)
- [x] Better fusion (swept alpha 0.5-0.7, sigma 0.15/0.25, relevance floor 0-0.6; current alpha 0.5 sigma 0.15 stays best on harmonic mean 0.514; floor kept as optional min_rel). Follow-up idea: RRF and learning-to-rank: rerank only top-N relevant (e.g. require BM25 >= x% of max), reciprocal-rank fusion, or learning-to-rank; sweep alpha/sigma; pick the setting that maximizes a combined metric (e.g. harmonic mean of nDCG@10 and level match).
- [x] Adaptive target (wired into /api/feedback; offline simulation done: gap to ideal difficulty 0.264 -> 0.136) from feedback (too easy / too hard) and looked-up words.
- [ ] (stem-for-BM25-only split into reranker-unstemmed still open) Report every experiment in data/eval_report.md with before/after numbers.
- [x] Level match in evaluate.py/grad_eval.py is judged with the current model's own difficulty, so it is circular across difficulty models; add a fixed reference judge (e.g. held-out source labels or a frozen model) for fair comparisons. (Done: grad_eval reports gold_level, source-label level fit, as the model-independent judge.)
- [x] Difficulty calibration (percentile rank per language, env LL_CALIBRATE=1; off by default, see CHANGELOG).

## Website version (priority)
- Static web version, split into small steps (one per run):
  - [x] W1: `python -m lingualadder.export_web` writes web/data/<lang>.json (id, title, url, 300-char snippet, difficulty, level, term postings for top-N terms) for en and es; check size.
  - [x] W2 (done early; parity 27/27 with Python via `node web/parity_test.js`): web/index.html + web/app.js: profile (language, level), BM25 + reranker in JS matching search.py; verify top-10 matches Python for 5 queries.
  - [x] W3 (side-by-side compare done; full-article link done; badges + plain-BM25 toggle already in; reader view DONE): link to full Wikipedia article.
  - [ ] W4: ("/" focus shortcut + empty-results message added) (aria-live status + select labels added) (mobile CSS + focus styles added) en/es only now (web data 6.3 MB raw); remaining: browser test on mobile width, publish as Hark Page.
  - [x] W5a: single-file build (python -m lingualadder.build_single [langs]) embeds chosen languages; Hark Pages allow one HTML file only (hi = 0.75 MB).
  - [x] W5b (published as Hark Page "LinguaLadder", en+es, 6.5 MB; later runs use edit): publish dist/lingualadder.html (hi, maybe en trimmed) as Hark Page; original W5: publish web/ as Hark Page "LinguaLadder" (size check passed: ~14.7 MB raw; load only the selected language).
- [ ] (umbrella) Static web version in `web/` that runs fully in the browser (no server): export a compact JSON index per language (doc ids, titles, snippets, difficulty, BM25 postings or precomputed term stats), JS BM25 + level-aware re-ranker identical to search.py, profile (language, level), results with level badges, reader view, BM25 comparison toggle.
- [x] Keep exported data small enough to host (target < 15 MB total; trim text to a snippet + link to Wikipedia for full article).
- [x] Publish/update it as a Hark Page (website_coding_agent) once it works locally.
- [ ] Mobile-friendly layout, accessible colors, fast first load. (remembered profile + shareable ?q= links added)

## Search quality
- [x] Tune ALPHA and SIGMA with the eval harness (grid in CHANGELOG; current default is on the best harmonic-mean frontier, kept).
- [x] Query expansion / stemming (Snowball en/es, opt-in LL_STEM=1; BM25 P@10 0.745->0.756 but LL nDCG 0.737->0.714, so off by default). Follow-up: stem only for BM25 stage, keep reranker snippets unstemmed.
- [ ] Personalize with looked-up words (vocab-aware re-ranking): (DONE: evaluated for en and es with simulated learners, default beta 0.5 whenever a known-word set is given, see CHANGELOG; remaining: wire to UI lookups in web and Flask, then web port of the term)
- [ ] CEFR mapping: (band distribution in web status line; cefr_label helper added; band shown in web UI; Flask UI now shows band; bands now corpus-quantile calibrated; remaining: validate vs gold CEFR texts) on top of Beginner/Intermediate/Advanced.

## Engineering
- [x] Unit tests for textproc, BM25, re-ranker (pytest). (DONE: app, textproc, BM25, reranker; 10 tests)
- [ ] Faster startup (smaller index, lazy load).
- [x] Input validation (400 on bad values); 404/500 error pages done.
- [ ] README kept current.

- [x] CEFR: validate bands against externally CEFR-labelled texts instead of corpus quantiles (DONE: lingualadder.cefr_validate, per-language cuts; en works, es weak).
- [ ] CEFR-es: the Spanish difficulty score barely tracks CEFR (Spearman 0.18 on Kwiziq; a ridge head on the 15 features reaches 0.51 in cross-validation but does not transfer to long articles). Needs more Spanish CEFR-labelled documents (A1-C2, esp. C2) or a Spanish-specific head; then re-fit the es cuts.
- [ ] CEFR-top: en/es corpus articles pile into the top bands (en 67% C2, es 83% C1); consider splitting the upper range by within-corpus quantile for display.
- [x] Adaptive target step/tolerance sweep done (see CHANGELOG; step 0.07 kept).
- [x] Adaptive target: decaying step and noisy learner simulated (see CHANGELOG). Follow-up: try default step 0.10-0.15 with decay 0.95.

## Expanded corpus (data priority, in progress)
- [x] E1: collect_big finished (en 5,500 + es 5,500 regular, Simple English, Vikidia); finalize now keeps every article (no cap), raw files split into parts under 20 MB.
- [x] E2: coverage fill rounds (parallel search, incremental writes): en 303/304 and es 286/304 topics with all three levels (was 189 and 141 of 304 after the uncapped build).
- [x] E3: wait for boost_es (Spanish growth to English size) to finish, merge it (python -m lingualadder.boost_es --merge), rebuild, run python -m lingualadder.coverage --fill --rounds 2 --per-gap 12 until 304/304 or report the topics that cannot be filled.
- [ ] E4: evaluate.py, grad_eval.py (with and without topic guard), export_web en es (split JSON over 24 MB), tests + node tests, docs/README numbers, CHANGELOG "Expanded corpus", GitHub sync, Hark Page (smaller sample), zip.

- [ ] E5 (step 2 done: targeted per-topic search terms closed every coverage gap, en 304/304 and es 304/304; step 1: GitHub sync of code and small files done; web data is 45 MB so it stays out of Pages, files over 25 MB cannot be web-uploaded): add a second easy Spanish source (children's encyclopedias) to close the 131 easy-article gap and fill the 10 remaining es gap topics.

- [x] W6: Spanish and English interface (web/i18n.js, "Interface" selector, remembered, defaults to the browser language; 82 strings each, node web/i18n_test.js); Spanish topic chips now use Spanish labels for all 304 topics (python -m lingualadder.topic_labels).
- [x] W7: Flask UI in Spanish too (DONE: lingualadder/flask_i18n.py, EN/ES switch, Accept-Language default, Spanish topic labels, reader script text; the Hark Page runs the static web version, which already had the Spanish interface).
- [x] W9: tap-to-look-up words in the web results (Wiktionary in the interface language, 'New word' marks feed the known-word set and re-rank), 'My new words' list, mobile CSS fixes ported into web/style.css (44px tap targets, darker light-mode level colours, hero fallback colour); remaining: real-device browser check of the Hark Page.
- [x] W8: the vocab-aware term (beta 0.5) is now used in both UIs: known words = N most frequent words of the level (300/1,500/5,000) minus looked-up words (Flask vocab table); ported to web/ll.js with parity (45/45 incl. vocab cases) and a "Prefer snippets made of words I know" switch. Remaining: real lookups in the web reader (the web version links out to Wikipedia, so it has no looked-up words yet).
