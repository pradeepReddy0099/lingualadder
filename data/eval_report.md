# LinguaLadder evaluation

## Corpus

| Language | Articles |
|---|---|
| en | 992 |
| es | 756 |

## 1. Difficulty model (easy vs. regular)

| Setting | Accuracy | F1 |
|---|---|---|
| 5-fold CV, all features | 0.888 | 0.929 |
| 5-fold CV, baseline (sentence + word length) | 0.776 | 0.867 |
| Test on unseen language: es, all features | 0.827 | 0.89 |
| Test on unseen language: es, baseline | 0.762 | 0.856 |
| Test on unseen language: en, all features | 0.884 | 0.928 |
| Test on unseen language: en, baseline | 0.769 | 0.868 |

Feature weights (positive = harder): log_length 1.319, avg_sentence_len 1.03, rare_word_share 0.765, digit_rate 0.71, core_vocab_share -0.662, sentence_len_std 0.534, long_sentence_share 0.438, avg_word_len -0.411, long_word_share 0.271, mid_band_share -0.269, syllables_per_word 0.256, commas_per_sentence -0.208, parens_per_sentence -0.129, type_token_ratio 0.098, subord_per_sentence -0.055

## 2-3. Retrieval and level match (top 10, averaged over levels)

| Language | Queries | Level | P@10 BM25 | P@10 LL | nDCG@10 BM25 | nDCG@10 LL | Level match BM25 | Level match LL |
|---|---|---|---|---|---|---|---|---|
| en | 47 | beginner | 0.943 | 0.755 | 0.955 | 0.762 | 0.1 | 0.345 |
| en | 47 | intermediate | 0.943 | 0.766 | 0.955 | 0.756 | 0.104 | 0.306 |
| en | 47 | advanced | 0.943 | 0.781 | 0.955 | 0.808 | 0.272 | 0.609 |
| es | 47 | beginner | 0.787 | 0.711 | 0.884 | 0.784 | 0.097 | 0.188 |
| es | 47 | intermediate | 0.787 | 0.685 | 0.884 | 0.743 | 0.066 | 0.181 |
| es | 47 | advanced | 0.787 | 0.683 | 0.884 | 0.773 | 0.331 | 0.526 |

**Overall:** P@10 0.865 → 0.73, nDCG@10 0.92 → 0.771, level match 0.162 → 0.359 (BM25 → LinguaLadder).

## Alpha sweep (alpha = weight on relevance)

| alpha | P@10 | nDCG@10 | Level match |
|---|---|---|---|
| 1.0 | 0.865 | 0.92 | 0.162 |
| 0.8 | 0.841 | 0.892 | 0.24 |
| 0.6 | 0.778 | 0.821 | 0.312 |
| 0.5 | 0.73 | 0.771 | 0.359 |
| 0.4 | 0.689 | 0.727 | 0.391 |
| 0.2 | 0.631 | 0.664 | 0.421 |
> Scope note: en+es only from this point; numbers are not comparable to the earlier five-language runs.
