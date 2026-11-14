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
| en | 152 | beginner | 0.801 | 0.718 | 0.819 | 0.723 | 0.113 | 0.375 |
| en | 152 | intermediate | 0.801 | 0.726 | 0.819 | 0.735 | 0.131 | 0.346 |
| en | 152 | advanced | 0.801 | 0.73 | 0.819 | 0.745 | 0.41 | 0.757 |
| es | 179 | beginner | 0.731 | 0.678 | 0.764 | 0.695 | 0.096 | 0.28 |
| es | 179 | intermediate | 0.731 | 0.653 | 0.764 | 0.668 | 0.124 | 0.293 |
| es | 179 | advanced | 0.731 | 0.666 | 0.764 | 0.687 | 0.457 | 0.708 |

**Overall:** P@10 0.766 → 0.695, nDCG@10 0.792 → 0.709, level match 0.222 → 0.46 (BM25 → LinguaLadder).

## Alpha sweep (alpha = weight on relevance)

| alpha | P@10 | nDCG@10 | Level match |
|---|---|---|---|
| 1.0 | 0.776 | 0.804 | 0.225 |
| 0.8 | 0.758 | 0.781 | 0.35 |
| 0.6 | 0.709 | 0.727 | 0.445 |
| 0.5 | 0.695 | 0.709 | 0.46 |
| 0.4 | 0.686 | 0.695 | 0.467 |
| 0.2 | 0.667 | 0.673 | 0.475 |