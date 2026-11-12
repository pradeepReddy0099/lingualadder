import math
from lingualadder.search import BM25Index, LinguaLadder


def test_bm25_ranks_matching_doc_first_and_idf():
    idx = BM25Index().build([["cat", "dog"], ["cat", "cat", "fish"], ["bird"]])
    s = idx.score(["cat"])
    assert set(s) == {0, 1} and s[1] > s[0]
    assert idx.idf["bird"] > idx.idf["cat"]
    assert idx.score(["zzz"]) == {}


def _ll():
    ll = LinguaLadder.__new__(LinguaLadder)
    mk = lambda i, d: {"id": str(i), "title": "Volcano", "url": "u", "difficulty": d, "level": "x",
                       "source": "s", "topic": "", "snippet": "", "words": 5}
    ll.docs = {"en": [mk(0, 0.2), mk(1, 0.8)]}
    ll.indexes = {"en": BM25Index().build([["volcano"], ["volcano"]])}
    return ll


def test_reranker_prefers_target_level():
    ll = _ll()
    assert ll.search("en", "volcano", 0.2)[0]["id"] == "0"
    assert ll.search("en", "volcano", 0.8)[0]["id"] == "1"
    r = ll.search("en", "volcano", 0.2, rerank=False)
    assert all(math.isclose(x["score"], 1.0) for x in r)


def test_min_rel_and_exclude():
    ll = _ll()
    assert [r["id"] for r in ll.search("en", "volcano", 0.2, exclude=("0",))] == ["1"]


def test_on_topic_articles_rank_before_passing_mentions():
    ll = LinguaLadder.__new__(LinguaLadder)
    mk = lambda i, t, d: {"id": str(i), "title": t, "url": "u", "difficulty": d, "level": "x",
                          "source": "s", "topic": "", "snippet": "", "words": 5}
    # doc 0 mentions "dog" a lot but is about bread and sits on the learner's level; doc 1 is about dogs.
    ll.docs = {"en": [mk(0, "Soda bread", 0.2), mk(1, "Dog", 0.9)]}
    ll.indexes = {"en": BM25Index().build([["dog", "dog", "dog", "bread"], ["dog", "pet"]])}
    r = ll.search("en", "dog", 0.2)
    assert [x["id"] for x in r] == ["1", "0"] and r[0]["on_topic"] and not r[1]["on_topic"]
    assert ll.search("en", "dog", 0.2, on_topic_first=False, topic_weight=0.0)[0]["id"] == "0"
