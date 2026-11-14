"""Estimated known-word set of a learner, used by the vocabulary-aware term of search().

Words are ranked by how many article openings (snippets) contain them, ties broken alphabetically
(so the static web version builds the identical list). A learner at a level is assumed to know the
N most frequent words (VOCAB_SIZES), minus any word they looked up (those are not known yet).
"""
from collections import Counter

from .config import VOCAB_SIZES
from .textproc import index_tokens


def ranked_words(docs, lang):
    df = Counter()
    for d in docs:
        df.update(set(index_tokens(d["snippet"], lang)))
    return [w for w, _ in sorted(df.items(), key=lambda x: (-x[1], x[0]))]


def known_set(ranked, level, unknown_terms=(), lang="en"):
    known = set(ranked[:VOCAB_SIZES[level]])
    for t in unknown_terms:
        known.difference_update(index_tokens(t, lang))
    return known
