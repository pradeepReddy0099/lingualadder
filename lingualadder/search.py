"""BM25 retrieval plus level-aware re-ranking (the core LinguaLadder algorithm).

final(d) = ALPHA * bm25(d) / max_bm25  +  (1 - ALPHA) * exp(-(diff(d) - t)^2 / (2 * SIGMA^2))

where diff(d) in [0, 1] is the article's predicted difficulty and t is the
learner's target level.
"""
import json
import math
import pickle
from collections import Counter, defaultdict

import numpy as np

from .config import ALPHA, CANDIDATES, DATA_DIR, ON_TOPIC_FIRST, ON_TOPIC_MIN, SIGMA, TOPIC_WEIGHT
from .textproc import index_tokens


class BM25Index:
    def __init__(self, k1=1.2, b=0.75):
        self.k1, self.b = k1, b
        self.postings = defaultdict(list)   # term -> [(doc_idx, tf)]
        self.doc_len = []
        self.idf = {}
        self.avgdl = 0.0

    def build(self, token_lists):
        df = Counter()
        for i, toks in enumerate(token_lists):
            tf = Counter(toks)
            self.doc_len.append(len(toks))
            for term, c in tf.items():
                self.postings[term].append((i, c))
            df.update(tf.keys())
        n = len(token_lists)
        self.avgdl = sum(self.doc_len) / max(n, 1)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.postings = dict(self.postings)
        return self

    def score(self, query_tokens):
        scores = defaultdict(float)
        for term in set(query_tokens):
            if term not in self.postings:
                continue
            idf = self.idf[term]
            for i, tf in self.postings[term]:
                dl = self.doc_len[i]
                scores[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return scores


import os
CALIBRATE = os.environ.get("LL_CALIBRATE", "0") == "1"


class LinguaLadder:
    """Holds one BM25 index and document table per language."""

    def __init__(self, path=DATA_DIR / "index.pkl"):
        with open(path, "rb") as f:
            blob = pickle.load(f)
        self.docs = blob["docs"]          # {lang: [doc dicts]}
        self.indexes = blob["indexes"]    # {lang: BM25Index}
        if CALIBRATE:
            for docs in self.docs.values():  # percentile-rank difficulty so targets split the corpus evenly
                order = np.argsort(np.argsort([d["difficulty"] for d in docs]))
                for d, r in zip(docs, order):
                    d["raw_difficulty"] = d["difficulty"]
                    d["difficulty"] = float((r + 0.5) / len(docs))

    def languages(self):
        return sorted(self.docs)

    def bm25(self, lang, query, k=CANDIDATES):
        scores = self.indexes[lang].score(index_tokens(query, lang))
        return sorted(scores.items(), key=lambda x: -x[1])[:k]

    def _topical(self, lang, d, qterms):
        """Share of query terms in the article's title (full credit) or its opening lead (half credit).

        A word that only appears somewhere in the body is a passing mention, not what the article is about.
        """
        if not qterms:
            return 0.0
        key = "_tl"
        if key not in d:
            d[key] = (set(index_tokens(d["title"], lang)), set(index_tokens(d.get("snippet", ""), lang)))
        title, lead = d[key]
        idf = self.indexes[lang].idf  # rarer query words count more ("rome" over "history")
        tot = sum(idf[t] for t in qterms) or 1.0
        return sum(idf[t] * (1.0 if t in title else 0.5 if t in lead else 0.0) for t in qterms) / tot

    def search(self, lang, query, target, alpha=ALPHA, sigma=SIGMA, k=10, rerank=True, exclude=(), min_rel=0.0,
               known=None, beta=0.0, topic_weight=TOPIC_WEIGHT, on_topic_first=ON_TOPIC_FIRST):
        cands = self.bm25(lang, query)
        if not cands:
            return []
        top = cands[0][1] or 1.0
        idx = self.indexes[lang]
        qterms = {t for t in index_tokens(query, lang) if t in idx.postings}
        results = []
        for i, s in cands:
            d = self.docs[lang][i]
            if d["id"] in exclude:
                continue
            topical = self._topical(lang, d, qterms) if rerank else 1.0  # plain BM25 baseline stays untouched
            rel = (1 - topic_weight) * (s / top) + topic_weight * topical if rerank else s / top
            fit = math.exp(-((d["difficulty"] - target) ** 2) / (2 * sigma ** 2))
            final = alpha * rel + (1 - alpha) * fit if rerank else rel
            if rerank and known and beta:  # opt-in vocab-aware: favor snippets mostly made of words the learner knows
                toks = index_tokens(d["snippet"], lang)
                if toks:
                    final += beta * (sum(t in known for t in toks) / len(toks) - 0.5)
            if rerank and rel < min_rel:
                final -= 1.0  # below the relevance floor: only after every on-topic doc
            if rerank and on_topic_first and topical < ON_TOPIC_MIN:
                final = rel - 2.0  # mentions the word but is not about it: after every on-topic article
            results.append({**{x: d[x] for x in ("id", "title", "url", "difficulty", "level", "source",
                                                  "topic", "snippet", "words")},
                            "bm25": round(s, 3), "relevance": round(rel, 3), "fit": round(fit, 3),
                            "on_topic": topical >= ON_TOPIC_MIN,
                            "score": round(final, 4)})
        results.sort(key=lambda r: -r["score"])
        return results[:k]

    def get(self, lang, doc_id):
        for d in self.docs[lang]:
            if d["id"] == doc_id:
                return d
        return None


def adapt_target(target, feedback, step=0.05, lo=0.0, hi=1.0):
    """Shift the learner's target difficulty from 'too_easy'/'too_hard' feedback.

    Each 'too_easy' raises the target by `step`, each 'too_hard' lowers it;
    the result is clamped to [lo, hi].
    """
    for f in feedback:
        if f == "too_easy":
            target += step
        elif f == "too_hard":
            target -= step
    return min(hi, max(lo, target))


CEFR_BANDS = [(0.20, "A1"), (0.61, "A2"), (0.87, "B1"), (0.94, "B2"), (0.98, "C1"), (1.01, "C2")]  # corpus-quantile cutoffs (10/25/45/65/85%)


def cefr_label(difficulty):
    """Map a 0-1 difficulty score to an approximate CEFR band (A1-C2)."""
    d = min(max(float(difficulty), 0.0), 1.0)
    for hi, lab in CEFR_BANDS:
        if d < hi:
            return lab
    return "C2"
