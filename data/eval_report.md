# LinguaLadder evaluation

## Corpus

| Language | Articles |
|---|---|
| en | 8282 |
| es | 8109 |

## 1. Difficulty model (easy vs. regular)

| Setting | Accuracy | F1 |
|---|---|---|
| 5-fold CV, all features | 0.866 | 0.914 |
| 5-fold CV, baseline (sentence + word length) | 0.777 | 0.865 |
| Test on unseen language: es, all features | 0.814 | 0.881 |
| Test on unseen language: es, baseline | 0.745 | 0.843 |
| Test on unseen language: en, all features | 0.882 | 0.925 |
| Test on unseen language: en, baseline | 0.765 | 0.862 |

Feature weights (positive = harder): core_vocab_share -2.088, rare_word_share -1.266, mid_band_share -1.127, log_length 1.101, avg_sentence_len 0.629, sentence_len_std 0.511, long_word_share 0.435, digit_rate 0.423, avg_word_len -0.411, long_sentence_share 0.389, syllables_per_word 0.231, commas_per_sentence -0.178, parens_per_sentence 0.1, subord_per_sentence -0.028, type_token_ratio -0.019

## 2-3. Retrieval and level match (top 10, averaged over levels)

| Language | Queries | Level | P@10 BM25 | P@10 LL | nDCG@10 BM25 | nDCG@10 LL | Level match BM25 | Level match LL |
|---|---|---|---|---|---|---|---|---|
| en | 152 | beginner | 0.805 | 0.724 | 0.824 | 0.73 | 0.115 | 0.374 |
| en | 152 | intermediate | 0.805 | 0.73 | 0.824 | 0.741 | 0.125 | 0.328 |
| en | 152 | advanced | 0.805 | 0.733 | 0.824 | 0.747 | 0.375 | 0.716 |
| es | 179 | beginner | 0.744 | 0.694 | 0.777 | 0.71 | 0.096 | 0.259 |
| es | 179 | intermediate | 0.744 | 0.672 | 0.777 | 0.687 | 0.122 | 0.289 |
| es | 179 | advanced | 0.744 | 0.687 | 0.777 | 0.704 | 0.434 | 0.682 |

**Overall:** P@10 0.774 → 0.707, nDCG@10 0.8 → 0.72, level match 0.211 → 0.441 (BM25 → LinguaLadder).

## Alpha sweep (alpha = weight on relevance)

| alpha | P@10 | nDCG@10 | Level match |
|---|---|---|---|
| 1.0 | 0.785 | 0.814 | 0.214 |
| 0.8 | 0.767 | 0.791 | 0.337 |
| 0.6 | 0.722 | 0.739 | 0.426 |
| 0.5 | 0.707 | 0.72 | 0.441 |
| 0.4 | 0.696 | 0.708 | 0.449 |
| 0.2 | 0.679 | 0.686 | 0.456 |