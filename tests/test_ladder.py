from app import app, ENGINE
from lingualadder.ladder import ladder_strip, read_next


def _r(level, rel, on=True, i=0):
    return {"id": f"{level}{i}", "level": level, "relevance": rel, "on_topic": on, "title": level}


def test_ladder_picks_most_relevant_on_topic_per_level():
    res = [_r("beginner", .5, i=1), _r("beginner", .9, i=2), _r("beginner", .99, on=False, i=3), _r("advanced", .4)]
    g = {x["level"]: x["doc"] for x in ladder_strip(res)}
    assert g["beginner"]["id"] == "beginner2" and g["intermediate"] is None and g["advanced"]["id"] == "advanced0"
    assert ladder_strip([_r("beginner", .5, on=False)]) == []


def test_read_next_goes_up_then_nearest():
    docs = [{"id": s, "topic": "t", "difficulty": d} for s, d in (("a", .2), ("b", .5), ("c", .7), ("d", .9)) ] + [{"id": "z", "topic": "u", "difficulty": .6}]
    n, up = read_next(docs, docs[1]); assert n["id"] == "c" and up
    n, up = read_next(docs, docs[1], read_ids=["c"]); assert n["id"] == "d" and up
    n, up = read_next(docs, docs[3], read_ids=["c"]); assert n["id"] == "b" and not up  # nothing harder: nearest unread
    n, up = read_next(docs, docs[3], read_ids=["a", "b", "c"]); assert n is None


def test_flask_ladder_and_read_next_en_es():
    for lang, ui, h, nx in (("en", "en", "The ladder for this topic", "Next up:"), ("es", "es", "La escalera de este tema", "Siguiente:")):
        c = app.test_client(); c.get(f"/ui/{ui}")
        c.post("/", data={"target": lang, "native": "en", "level": "beginner"})
        q = "volcano" if lang == "en" else "volcán"
        html = c.get(f"/search?q={q}").get_data(as_text=True)
        assert h in html and html.count('class="rung ') == 3
        assert 'class="rung' not in c.get(f"/search?q={q}&compare=1").get_data(as_text=True)
        link = html.split('<div class="rung beginner">')[1].split('href="')[1].split('"')[0]
        page = c.get(link).get_data(as_text=True)
        assert nx in page or ("You have read everything" in page or "Ya has le" in page)
        nxt = page.split(nx)[1].split('href="')[1].split('"')[0]
        assert c.get(nxt).status_code == 200
