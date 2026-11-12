from lingualadder.search import LinguaLadder, index_tokens

def test_known_words_boost():
    ll = LinguaLadder()
    base = ll.search("en", "volcano", 0.5, k=10)
    known = set()
    for r in base[5:]:
        known |= set(index_tokens(r["snippet"], "en"))
    boosted = ll.search("en", "volcano", 0.5, k=10, known=known, beta=1.0)
    assert len(boosted) == 10
    assert [r["id"] for r in boosted] != [r["id"] for r in base]
