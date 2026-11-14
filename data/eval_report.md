# LinguaLadder evaluation

## Corpus

| Language | Articles |
|---|---|
| en | 8408 |
| es | 8800 |

## 1. Difficulty model (easy vs. regular)

| Setting | Accuracy | F1 |
|---|---|---|
| 5-fold CV, all features | 0.86 | 0.91 |
| 5-fold CV, baseline (sentence + word length) | 0.772 | 0.862 |
| Test on unseen language: en, all features | 0.879 | 0.923 |
| Test on unseen language: en, baseline | 0.758 | 0.859 |
| Test on unseen language: es, all features | 0.804 | 0.874 |
| Test on unseen language: es, baseline | 0.739 | 0.839 |

Feature weights (positive = harder): core_vocab_share -2.058, rare_word_share -1.217, mid_band_share -1.094, log_length 1.025, avg_sentence_len 0.63, sentence_len_std 0.54, long_word_share 0.44, avg_word_len -0.416, digit_rate 0.397, long_sentence_share 0.374, syllables_per_word 0.209, commas_per_sentence -0.202, parens_per_sentence 0.088, subord_per_sentence -0.056, type_token_ratio -0.03

## 2-3. Retrieval and level match (top 10, averaged over levels)

| Language | Queries | Level | P@10 BM25 | P@10 LL | nDCG@10 BM25 | nDCG@10 LL | Level match BM25 | Level match LL |
|---|---|---|---|---|---|---|---|---|
| en | 152 | beginner | 0.801 | 0.739 | 0.819 | 0.784 | 0.113 | 0.362 |
| en | 152 | intermediate | 0.801 | 0.747 | 0.819 | 0.79 | 0.131 | 0.334 |
| en | 152 | advanced | 0.801 | 0.755 | 0.819 | 0.803 | 0.41 | 0.7 |
| es | 179 | beginner | 0.731 | 0.694 | 0.764 | 0.75 | 0.096 | 0.268 |
| es | 179 | intermediate | 0.731 | 0.678 | 0.764 | 0.738 | 0.124 | 0.285 |
| es | 179 | advanced | 0.731 | 0.698 | 0.764 | 0.756 | 0.457 | 0.655 |

**Overall:** P@10 0.766 → 0.719, nDCG@10 0.792 → 0.77, level match 0.222 → 0.434 (BM25 → LinguaLadder).

## Alpha sweep (alpha = weight on relevance)

| alpha | P@10 | nDCG@10 | Level match |
|---|---|---|---|
| 1.0 | 0.78 | 0.824 | 0.226 |
| 0.8 | 0.766 | 0.811 | 0.339 |
| 0.6 | 0.73 | 0.781 | 0.42 |
| 0.5 | 0.719 | 0.77 | 0.434 |
| 0.4 | 0.71 | 0.756 | 0.441 |
| 0.2 | 0.692 | 0.723 | 0.458 |