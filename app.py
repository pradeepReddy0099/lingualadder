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


@app.context_processor
def inject():
    return {"LANGUAGES": LANGUAGES, "NATIVE": NATIVE_LANGUAGES, "LEVELS": LEVELS, "profile": session.get("profile")}


@app.route("/", methods=["GET", "POST"])
def home():
    profile()
    if request.method == "POST":
        langs = set(ENGINE.docs)
        tgt = request.form.get("target", "")
        nat = request.form.get("native", "")
        lvl = request.form.get("level", "")
        if tgt not in langs or nat not in langs | {"te", "en"} or lvl not in ("beginner", "intermediate", "advanced"):
            return "Invalid profile: choose a supported language and level.", 400
        session["profile"] = {"target": tgt, "native": nat, "level": lvl, "offset": 0.0}
        return redirect(url_for("search"))
    topics = sorted({d["topic"] for docs in ENGINE.docs.values() for d in docs if d.get("topic")})
    stats = {lang: len(docs) for lang, docs in ENGINE.docs.items()}
    return render_template("home.html", topics=topics, stats=stats)


@app.route("/search")
def search():
    p = profile()
    if not p:
        return redirect(url_for("home"))
    q = request.args.get("q", "").strip()
    in_native = request.args.get("native") == "1"
    results, used_query, compare = [], q, request.args.get("compare") == "1"
    baseline = []
    if q:
        if in_native and p["native"] != p["target"]:
            tr = translate(q, p["native"], p["target"])
            used_query = tr["text"] or q
        target = target_of(p)
        results = ENGINE.search(p["target"], used_query, target)
        if compare:
            baseline = ENGINE.search(p["target"], used_query, target, rerank=False)
    return render_template("search.html", q=q, used_query=used_query, results=results, baseline=baseline,
                           compare=compare, in_native=in_native, target=round(target_of(p), 2))


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
    vocab = db().execute("SELECT term, translation FROM vocab WHERE uid=? AND lang=? ORDER BY ts DESC LIMIT 30",
                         (session["uid"], lang)).fetchall()
    return render_template("read.html", d=d, blocks=blocks, vocab=vocab)


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
    return "<!doctype html><title>Not found</title><h1>Page not found</h1><p><a href='/'>Back to LinguaLadder</a></p>", 404


@app.errorhandler(500)
def _server_error(e):
    return "<!doctype html><title>Error</title><h1>Something went wrong</h1><p><a href='/'>Back to LinguaLadder</a></p>", 500


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
