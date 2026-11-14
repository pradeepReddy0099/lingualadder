"""LinguaLadder web app.

Run:  python app.py   then open http://127.0.0.1:5000
"""
import os
import sqlite3
import time
import uuid

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for, abort

from lingualadder.config import ALPHA, DATA_DIR, LANGUAGES, LEVELS, NATIVE_LANGUAGES, SIGMA
from lingualadder.search import LinguaLadder
from lingualadder.textproc import strip_headings
from lingualadder import flask_i18n, placement as PL
from lingualadder.recommend import recommended
from lingualadder.ladder import ladder_strip, read_next
import random
from lingualadder.translate import translate

app = Flask(__name__)
from lingualadder.search import cefr_label
app.jinja_env.filters['cefr'] = cefr_label
app.secret_key = os.environ.get("SECRET_KEY", "lingualadder-dev-key")
ENGINE = LinguaLadder()
DB = DATA_DIR / "users.sqlite"


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.execute("CREATE TABLE IF NOT EXISTS vocab (uid TEXT, lang TEXT, term TEXT, translation TEXT, "
                     "doc_id TEXT, ts REAL, PRIMARY KEY (uid, lang, term))")
        g.db.execute("CREATE TABLE IF NOT EXISTS reads (uid TEXT, lang TEXT, doc_id TEXT, ts REAL, PRIMARY KEY (uid, lang, doc_id))")
        g.db.execute("CREATE TABLE IF NOT EXISTS feedback (uid TEXT, lang TEXT, doc_id TEXT, verdict TEXT, "
                     "difficulty REAL, ts REAL)")
    return g.db


@app.teardown_appcontext
def close_db(_):
    if "db" in g:
        g.db.close()


def profile():
    if "uid" not in session:
        session["uid"] = uuid.uuid4().hex
    p = session.get("profile")
    return p


def target_of(p):
    return min(0.95, max(0.05, LEVELS[p["level"]]["target"] + p.get("offset", 0.0)))


def ui_lang():
    ui = session.get("ui")
    if ui not in flask_i18n.UI_LANGS:
        ui = flask_i18n.detect(request.headers.get("Accept-Language"))
    return ui


@app.context_processor
def inject():
    ui = ui_lang()
    t = flask_i18n.make_t(ui)
    return {"LANGUAGES": LANGUAGES, "NATIVE": NATIVE_LANGUAGES, "LEVELS": LEVELS, "profile": session.get("profile"),
            "t": t, "ui": ui, "lname": lambda c, n=None: flask_i18n.lang_name(c, ui, n or NATIVE_LANGUAGES.get(c, c)), "UI_LANGS": flask_i18n.UI_LANGS,
            "reader_t": {k: t(k) for k in flask_i18n.READER_KEYS}}


@app.route("/ui/<lang>")
def set_ui(lang):
    if lang not in flask_i18n.UI_LANGS:
        abort(404)
    session["ui"] = lang
    back = request.referrer or url_for("home")
    return redirect(back)


@app.route("/", methods=["GET", "POST"])
def home():
    profile()
    if request.method == "POST":
        langs = set(ENGINE.docs)
        tgt = request.form.get("target", "")
        nat = request.form.get("native", "")
        lvl = request.form.get("level", "")
        if tgt not in langs or nat not in langs | {"te", "en"} or lvl not in ("beginner", "intermediate", "advanced"):
            return flask_i18n.make_t(ui_lang())("bad_profile"), 400
        session["profile"] = {"target": tgt, "native": nat, "level": lvl, "offset": 0.0}
        return redirect(url_for("search"))
    topics = sorted({d["topic"] for docs in ENGINE.docs.values() for d in docs if d.get("topic")})
    stats = {lang: len(docs) for lang, docs in ENGINE.docs.items()}
    if ui_lang() == "es":
        labels = flask_i18n.topic_labels_es()
        topics = sorted(labels.get(x, x) for x in topics)
    return render_template("home.html", topics=topics, stats=stats)


@app.route("/search")
def search():
    p = profile()
    if not p:
        return redirect(url_for("home"))
    q = request.args.get("q", "").strip()
    in_native = request.args.get("native") == "1"
    results, used_query, compare = [], q, request.args.get("compare") == "1"
    baseline, ladder = [], []
    if q:
        if in_native and p["native"] != p["target"]:
            tr = translate(q, p["native"], p["target"])
            used_query = tr["text"] or q
        target = target_of(p)
        # vocabulary-aware term: words of the learner's level are known, words they looked up are not
        looked_up = [r[0] for r in db().execute("SELECT term FROM vocab WHERE uid=? AND lang=?",
                                                     (session["uid"], p["target"])).fetchall()]
        known = ENGINE.known_words(p["target"], p["level"], looked_up)
        results = ENGINE.search(p["target"], used_query, target, known=known)
        if compare:
            baseline = ENGINE.search(p["target"], used_query, target, rerank=False)
        else:  # one on-topic pick per level, so every topic shows its easier and harder rungs
            ladder = ladder_strip(ENGINE.search(p["target"], used_query, target, k=100))
    read_ids = [r[0] for r in db().execute("SELECT doc_id FROM reads WHERE uid=? AND lang=?", (session["uid"], p["target"])).fetchall()]
    chips, n_topics = recommended(ENGINE.docs[p["target"]], p["target"], target_of(p), read_ids, n=None if request.args.get("topics") == "all" else 14)
    return render_template("search.html", q=q, used_query=used_query, results=results, baseline=baseline,
                           compare=compare, in_native=in_native, target=round(target_of(p), 2), lang=p["target"],
                           chips=chips, n_topics=n_topics, ladder=ladder, all_topics=request.args.get("topics") == "all")


# ---- Placement test: vocabulary checklist, then an adaptive cloze (same method as the web version)
def _place_apply(p, lang, res, vocab, cloze):
    from lingualadder.search import cefr_label
    lvl = res["level"]
    off = round(res["target"] - LEVELS[lvl]["target"], 3)
    p.update({"level": lvl, "offset": off, "place": {"lang": lang, "cefr": cefr_label(res["target"], lang),
              "vocab": round(vocab, 2), "cloze": round(cloze, 2), "target": round(res["target"], 3)}})
    session["profile"] = p


@app.route("/placement", methods=["GET", "POST"])
def placement():
    p = profile()
    if not p:
        return redirect(url_for("home"))
    lang, st = p["target"], session.get("pl")
    if request.method == "GET" and request.args.get("restart") == "1":
        st = None
        session.pop("pl", None)
    if request.method == "POST":
        act = request.form.get("act", "")
        if act == "start" or not st:
            st = {"seed": random.randrange(100000), "stage": "vocab", "n": 0}
        elif act == "vocab" and st["stage"] == "vocab":
            items = PL.vocab_items(ENGINE, lang, st["seed"])
            ticked = set(request.form.getlist("w"))
            st["vocab"] = PL.score_vocab(items, [it["word"] in ticked for it in items])
            st["sc"] = PL.Staircase().to_dict()
            st["used"], st["stage"] = [], "cloze"
        elif act in ("answer", "skip") and st["stage"] == "cloze" and st.get("item"):
            sc = PL.Staircase.from_dict(st["sc"])
            sc.record(act == "answer" and request.form.get("o") == st["item"]["answer"])
            st["sc"], st["item"] = sc.to_dict(), None
        if st["stage"] == "cloze" and not st.get("item"):
            sc = PL.Staircase.from_dict(st["sc"])
            item = None if sc.done() else PL.cloze_item(ENGINE, lang, sc.q, random.Random(st["seed"] * 31 + len(sc.history)), set(st["used"]))
            if item:
                st["used"].append(item["doc"])
                st["item"] = {k: item[k] for k in ("text", "options", "answer")}
            else:
                res = PL.combine(ENGINE, lang, st["vocab"], sc.estimate())
                _place_apply(p, lang, res, st["vocab"], sc.estimate())
                st["stage"] = "result"
        session["pl"] = st
        return redirect(url_for("placement"))
    if not st:
        return render_template("placement.html", stage="intro", lang=lang)
    if st["stage"] == "vocab":
        return render_template("placement.html", stage="vocab", lang=lang, items=PL.vocab_items(ENGINE, lang, st["seed"]), pct=5)
    if st["stage"] == "cloze":
        sc = PL.Staircase.from_dict(st["sc"])
        return render_template("placement.html", stage="cloze", lang=lang, item=st["item"], i=len(sc.history) + 1, n=sc.n,
                               pct=15 + round(75 * len(sc.history) / sc.n))
    return render_template("placement.html", stage="result", lang=lang, place=p.get("place") or {}, pct=100,
                           bands=["A1", "A2", "B1", "B2", "C1", "C2"])


@app.route("/read/<lang>/<path:doc_id>")
def read(lang, doc_id):
    p = profile()
    if not p:
        return redirect(url_for("home"))
    d = ENGINE.get(lang, doc_id)
    if not d:
        abort(404)
    paras = [x.strip() for x in d["text"].split("\n") if x.strip()]
    blocks = []
    for x in paras:
        if x.startswith("=="):
            blocks.append(("h", x.strip("= ").strip()))
        else:
            blocks.append(("p", x))
    read_ids = [r[0] for r in db().execute("SELECT doc_id FROM reads WHERE uid=? AND lang=?", (session["uid"], lang)).fetchall()]
    nxt, harder = read_next(ENGINE.docs[lang], d, read_ids)
    db().execute("INSERT OR REPLACE INTO reads VALUES (?,?,?,?)", (session["uid"], lang, d["id"], time.time()))
    db().commit()
    vocab = db().execute("SELECT term, translation FROM vocab WHERE uid=? AND lang=? ORDER BY ts DESC LIMIT 30",
                         (session["uid"], lang)).fetchall()
    return render_template("read.html", d=d, blocks=blocks, vocab=vocab, lang=lang, nxt=nxt, harder=harder)


@app.post("/api/translate")
def api_translate():
    p = profile()
    data = request.get_json(force=True)
    text = data.get("text", "")
    src, tgt = data.get("src") or p["target"], data.get("tgt") or p["native"]
    res = translate(text, src, tgt)
    ctx = (data.get("context") or "").strip()
    if ctx and len(text.split()) <= 3 and ctx != text:
        res["context"] = ctx
        res["context_translation"] = translate(ctx, src, tgt).get("text")
    if res.get("text") and len(text.split()) <= 6:
        db().execute("INSERT OR REPLACE INTO vocab VALUES (?,?,?,?,?,?)",
                     (session["uid"], p["target"], text.strip().lower(), res["text"], data.get("doc_id"), time.time()))
        db().commit()
    return jsonify(res)


@app.post("/api/feedback")
def api_feedback():
    p = profile()
    data = request.get_json(force=True)
    verdict = data["verdict"]  # too_easy | just_right | too_hard
    if verdict not in ("too_easy", "just_right", "too_hard"):
        abort(400)
    from lingualadder.search import adapt_target
    p["offset"] = round(adapt_target(p.get("offset", 0.0), [verdict], step=0.07, lo=-0.4, hi=0.4), 3)
    session["profile"] = p
    db().execute("INSERT INTO feedback VALUES (?,?,?,?,?,?)",
                 (session["uid"], p["target"], data.get("doc_id"), verdict, data.get("difficulty"), time.time()))
    db().commit()
    return jsonify({"target": round(target_of(p), 2), "offset": p["offset"]})


@app.route("/vocab")
def vocab():
    p = profile()
    if not p:
        return redirect(url_for("home"))
    rows = db().execute("SELECT lang, term, translation, ts FROM vocab WHERE uid=? ORDER BY ts DESC",
                        (session["uid"],)).fetchall()
    return render_template("vocab.html", rows=rows)


@app.route("/api/search")
def api_search():
    lang = request.args.get("lang", "en")
    level = request.args.get("level", "intermediate")
    q = request.args.get("q", "")
    if lang not in ENGINE.docs:
        return jsonify({"error": "unknown language"}), 400
    return jsonify(ENGINE.search(lang, q, LEVELS[level]["target"]))



@app.errorhandler(404)
def _not_found(e):
    t = flask_i18n.make_t(ui_lang())
    return f"<!doctype html><html lang='{ui_lang()}'><title>{t('nf_title')}</title><h1>{t('nf_h')}</h1><p><a href='/'>{t('back')}</a></p>", 404


@app.errorhandler(500)
def _server_error(e):
    t = flask_i18n.make_t(ui_lang())
    return f"<!doctype html><html lang='{ui_lang()}'><title>{t('err_title')}</title><h1>{t('err_h')}</h1><p><a href='/'>{t('back')}</a></p>", 500


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
