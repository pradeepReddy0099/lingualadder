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
| Test on unseen language: en, all features | 0.884 | 0.928 |
| Test on unseen language: en, baseline | 0.769 | 0.868 |
| Test on unseen language: es, all features | 0.827 | 0.89 |
| Test on unseen language: es, baseline | 0.762 | 0.856 |

Feature weights (positive = harder): log_length 1.319, avg_sentence_len 1.03, rare_word_share 0.765, digit_rate 0.71, core_vocab_share -0.662, sentence_len_std 0.534, long_sentence_share 0.438, avg_word_len -0.411, long_word_share 0.271, mid_band_share -0.269, syllables_per_word 0.256, commas_per_sentence -0.208, parens_per_sentence -0.129, type_token_ratio 0.098, subord_per_sentence -0.055

## 2-3. Retrieval and level match (top 10, averaged over levels)

| Language | Queries | Level | P@10 BM25 | P@10 LL | nDCG@10 BM25 | nDCG@10 LL | Level match BM25 | Level match LL |
|---|---|---|---|---|---|---|---|---|
| en | 47 | beginner | 0.943 | 0.928 | 0.955 | 0.924 | 0.1 | 0.162 |
| en | 47 | intermediate | 0.943 | 0.934 | 0.955 | 0.941 | 0.104 | 0.134 |
| en | 47 | advanced | 0.943 | 0.915 | 0.955 | 0.925 | 0.272 | 0.377 |
| es | 47 | beginner | 0.787 | 0.783 | 0.884 | 0.868 | 0.097 | 0.109 |
| es | 47 | intermediate | 0.787 | 0.781 | 0.884 | 0.868 | 0.066 | 0.072 |
| es | 47 | advanced | 0.787 | 0.77 | 0.884 | 0.863 | 0.331 | 0.35 |

**Overall:** P@10 0.865 → 0.852, nDCG@10 0.92 → 0.898, level match 0.162 → 0.201 (BM25 → LinguaLadder).

## Alpha sweep (alpha = weight on relevance)

| alpha | P@10 | nDCG@10 | Level match |
|---|---|---|---|
| 1.0 | 0.864 | 0.919 | 0.16 |
| 0.8 | 0.86 | 0.914 | 0.186 |
| 0.6 | 0.854 | 0.903 | 0.198 |
| 0.5 | 0.852 | 0.898 | 0.201 |
| 0.4 | 0.85 | 0.896 | 0.201 |
| 0.2 | 0.849 | 0.891 | 0.203 |