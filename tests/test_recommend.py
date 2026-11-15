from app import app
from lingualadder.recommend import rank_topics, recommended


def _docs(n, topic, diff):
    return [{"id": f"{topic}{i}", "topic": topic, "difficulty": diff, "title": topic} for i in range(n)]


def test_rank_prefers_topics_near_target_and_demotes_read():
    docs = _docs(5, "near", 0.5) + _docs(5, "far", 0.9) + _docs(2, "tiny", 0.5)
    r = rank_topics(docs, 0.5)
    assert [x[0] for x in r] == ["near", "far"]  # topics with fewer than 3 articles are skipped
    r2 = rank_topics(docs, 0.5, read_ids=[f"near{i}" for i in range(5)])
    assert r2[0][0] == "near" and r2[0][1] < r[0][1] and r2[0][4] == 5  # reading lowers the score, as in the browser


def test_topics_follow_level_en_es():
    from app import ENGINE
    for lang in ("en", "es"):
        docs = ENGINE.docs[lang]
        easy, _ = recommended(docs, lang, 0.15)
        hard, n = recommended(docs, lang, 0.85)
        assert n >= 250 and len(easy) == len(hard) == 14
        assert [c["topic"] for c in easy] != [c["topic"] for c in hard]
        assert all(c["label"] for c in easy + hard)


def test_chips_and_reading_history_in_flask():
    for lang, ui in (("en", "en"), ("es", "es")):
        c = app.test_client()
        c.get(f"/ui/{ui}")
        c.post("/", data={"target": lang, "native": "en", "level": "beginner"})
        html = c.get("/search").get_data(as_text=True)
        assert 'class="chip' in html and ("Recommended topics" if ui == "en" else "Temas recomendados") in html
        assert html.count('class="chip"') + html.count('class="chip seen"') >= 14
        assert c.get("/search?topics=all").get_data(as_text=True).count('class="chip') > 200
        first = html.split('class="chip" href="')[1].split('"')[0]
        assert c.get(first).status_code == 200


def test_share_rule_and_ladder_bonus():
    # a small topic that is all near beats a big topic that is mostly far; a climbable ladder gets a bonus
    docs = _docs(4, "small", 0.5) + _docs(1, "small", 0.1) + _docs(1, "small", 0.9)
    docs += _docs(2, "big", 0.5) + _docs(30, "big", 0.95)
    r = {x[0]: x for x in rank_topics(docs, 0.5)}
    assert r["small"][1] > r["big"][1]
    assert abs(r["small"][1] - (4 / 6 + 0.002 * 6 + 0.3)) < 1e-9   # near share + size term + ladder bonus
    assert abs(r["big"][1] - (2 / 32 + 0.002 * 32)) < 1e-9          # no easier article: no bonus


def test_chips_vary_with_level_in_both_languages():
    from app import ENGINE
    for lang in ("en", "es"):
        docs = ENGINE.docs[lang]
        seen = set()
        for t in (0.2, 0.35, 0.5, 0.65, 0.8):
            seen.update(c["topic"] for c in recommended(docs, lang, t)[0])
        assert len(seen) >= 30   # the old rule showed only 23 (es) different topics over nine levels
