"""Placement test (Flask side): item generation, scoring, simulated learners, and the full request flow, en and es."""
import math
import random
import re

import pytest

from app import app, ENGINE
from lingualadder import placement as PL


@pytest.mark.parametrize("lang", ["en", "es"])
def test_items_and_scoring(lang):
    v = PL.vocab_items(ENGINE, lang, 7)
    assert sum(x["real"] for x in v) == 18 and sum(not x["real"] for x in v) >= 5
    assert PL.vocab_items(ENGINE, lang, 7) == v                      # deterministic per seed
    assert PL.score_vocab(v, [x["real"] for x in v]) == 1
    assert PL.score_vocab(v, [True] * len(v)) == 0                   # saying yes to everything scores zero
    r, used, n = random.Random(3), set(), 0
    for q in (0.1, 0.3, 0.5, 0.7, 0.9):
        c = PL.cloze_item(ENGINE, lang, q, r, used)
        if c and "_____" in c["text"] and c["answer"] in c["options"] and len(set(c["options"])) == 4:
            n += 1
    assert n == 5


@pytest.mark.parametrize("lang", ["en", "es"])
def test_simulated_learners_ordered(lang):
    est = {}
    for ability in (0.15, 0.5, 0.85):
        e = []
        for s in range(25):
            r, st, used = random.Random(1000 + s * 7), PL.Staircase(), set()
            while not st.done():
                c = PL.cloze_item(ENGINE, lang, st.q, r, used)
                p = 0.25 + 0.75 / (1 + math.exp(-(ability - st.q) * 8))
                st.record(r.random() < p)
            e.append(st.estimate())
        est[ability] = sum(e) / len(e)
    assert est[0.15] < est[0.5] < est[0.85]
    assert abs(est[0.85] - 0.85) < 0.25 and est[0.15] < 0.45          # guessing floor biases weak learners up


def run_flow(lang, strong, ui="en"):
    c = app.test_client()
    c.get(f"/ui/{ui}")
    c.post("/", data={"target": lang, "native": "en", "level": "intermediate"})
    assert c.get("/placement").status_code == 200
    c.post("/placement", data={"act": "start"})
    page = c.get("/placement").get_data(as_text=True)
    words = re.findall(r'name="w" value="([^"]+)"', page)
    assert len(words) >= 23
    items = PL.vocab_items(ENGINE, lang, __import__("flask").session.get("pl", {}).get("seed", 0)) if False else None
    with c.session_transaction() as s:
        seed = s["pl"]["seed"]
    real = {x["word"] for x in PL.vocab_items(ENGINE, lang, seed) if x["real"]}
    c.post("/placement", data={"act": "vocab", "w": sorted(real) if strong else []})
    steps = 0
    while steps < 20:
        page = c.get("/placement").get_data(as_text=True)
        if 'class="big"' in page:
            break
        assert "_____" not in page and 'class="blank"' in page
        with c.session_transaction() as s:
            ans = s["pl"]["item"]["answer"]
        if strong:
            c.post("/placement", data={"act": "answer", "o": ans})
        else:
            c.post("/placement", data={"act": "skip"})
        steps += 1
    assert steps == 8
    with c.session_transaction() as s:
        return s["profile"]


@pytest.mark.parametrize("lang,ui", [("en", "en"), ("es", "es"), ("es", "en"), ("en", "es")])
def test_flow_changes_profile(lang, ui):
    strong, weak = run_flow(lang, True, ui), run_flow(lang, False, ui)
    assert strong["place"]["target"] > weak["place"]["target"] + 0.2
    assert weak["level"] == "beginner" and strong["level"] == "advanced"
    assert weak["place"]["cefr"] < strong["place"]["cefr"]            # "A1" < "C2" as strings
    c = app.test_client()
    c.post("/", data={"target": lang, "native": "en", "level": "intermediate"})
    with c.session_transaction() as s:
        s["profile"] = strong
    assert c.get("/search?q=volcano").status_code == 200


def test_spanish_texts_and_guards():
    c = app.test_client()
    assert c.get("/placement").status_code == 302                    # no profile yet
    c.get("/ui/es")
    c.post("/", data={"target": "es", "native": "en", "level": "beginner"})
    c.post("/placement", data={"act": "start"})
    page = c.get("/placement").get_data(as_text=True)
    assert "¿Cuáles de estas palabras conoces?" in page and "Which of these" not in page
    # answering out of order must not crash
    assert c.post("/placement", data={"act": "answer", "o": "x"}).status_code == 302
    assert c.get("/placement").status_code == 200


def _hist(pairs):
    return [{"q": q, "correct": bool(c)} for q, c in pairs]


def test_eap_matches_js_values_and_reduces_guessing_bias():
    h1 = _hist([(0.5, 1), (0.75, 0), (0.6, 1), (0.55, 0), (0.57, 1), (0.6, 0), (0.58, 1), (0.59, 0)])
    h2 = _hist([(0.5, 0), (0.25, 0), (0.1, 1), (0.2, 0), (0.15, 0), (0.1, 1), (0.1, 0), (0.06, 0)])
    assert abs(PL.eap_estimate(h1) - 0.447294) < 1e-5 and abs(PL.eap_estimate(h2) - 0.082269) < 1e-5   # same as web/placement.js
    assert 0.45 < PL.eap_estimate([]) < 0.55
    from lingualadder import placement_eval as PE
    sim = PE.simulate(8, 8, 60)
    old, new = PE.summarize(sim["mean4"]), PE.summarize(sim["eap"])
    assert new["mae"] < old["mae"] and new["mae_weak"] < old["mae_weak"]
    assert abs(new["bias"]["0.1"]) < abs(old["bias"]["0.1"])
