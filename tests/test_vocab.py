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


def _coverage(res, known, lang):
    covs = []
    for r in res:
        toks = index_tokens(r["snippet"], lang)
        covs.append(sum(t in known for t in toks) / len(toks) if toks else 0.0)
    return sum(covs) / len(covs)


def test_vocab_default_beta_raises_coverage_en_es():
    from collections import Counter
    ll = LinguaLadder()
    for lang, q in (("en", "history of rome"), ("es", "historia de roma")):
        df = Counter()
        for d in ll.docs[lang]:
            df.update(set(index_tokens(d["snippet"], lang)))
        known = {w for w, _ in df.most_common(1500)}
        plain = ll.search(lang, q, 0.5, k=10)
        aware = ll.search(lang, q, 0.5, k=10, known=known)  # default beta applies when known is given
        assert len(aware) == 10
        assert _coverage(aware, known, lang) >= _coverage(plain, known, lang)


def test_known_words_sizes_and_looked_up_removed():
    from lingualadder.search import LinguaLadder
    ll = LinguaLadder()
    for lang in ("en", "es"):
        b, i, a = (ll.known_words(lang, lv) for lv in ("beginner", "intermediate", "advanced"))
        assert len(b) == 300 and b < i < a
        w = sorted(b)[0]
        assert w not in ll.known_words(lang, "beginner", [w])


def test_flask_search_uses_looked_up_words_without_error():
    from app import app
    for lang in ("en", "es"):
        c = app.test_client()
        c.post('/', data={'target': lang, 'native': 'te', 'level': 'beginner'})
        r = c.get('/search?q=volcan' if lang == 'es' else '/search?q=volcano')
        assert r.status_code == 200
