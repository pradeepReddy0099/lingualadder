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
