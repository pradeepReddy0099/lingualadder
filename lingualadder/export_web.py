"""Export a compact per-language JSON index for the static, in-browser version (web/).

python -m lingualadder.export_web [lang ...]

File layout (web/data/<lang>.json):
  {"lang", "n", "avgdl", "k1", "b", "alpha", "sigma", "topic_weight", "on_topic_min", "on_topic_first", "targets",
   "docs":  [[id, title, url, snippet, difficulty, level, words, topic, source], ...],
   "dl":    [doc_len, ...],
   "terms": {term: [idf, d0, tf0, d1-d0, tf1, ...]}}     (doc ids delta-coded, tf as ints)
The JS side recomputes BM25 exactly as search.py does, then applies the same reranker.
"""
import json
import sys

from .config import ALPHA, CANDIDATES, DATA_DIR, LEVELS, ON_TOPIC_FIRST, ON_TOPIC_MIN, SIGMA, TOPIC_WEIGHT
from .search import LinguaLadder
from .textproc import STOP, is_cjk

WEB_DATA = DATA_DIR.parent / "web" / "data"
DEFAULT_LANGS = ["en", "es"]


def export_lang(ll, lang):
    docs = ll.docs[lang]
    ix = ll.indexes[lang]
    terms = {}
    for t, plist in ix.postings.items():
        plist = sorted(plist)
        if is_cjk(lang) and len(plist) < 2:
            continue  # drop df=1 terms for CJK to shrink the file
        flat, prev = [round(ix.idf[t], 3)], 0
        for i, tf in plist:
            flat += [i - prev, tf]
            prev = i
        terms[t] = flat
    out = {
        "lang": lang, "n": len(docs), "avgdl": round(ix.avgdl, 3), "k1": ix.k1, "b": ix.b,
        "cjk": is_cjk(lang), "stop": sorted(STOP.get(lang, ())), "candidates": CANDIDATES, "alpha": ALPHA, "sigma": SIGMA, "topic_weight": TOPIC_WEIGHT, "on_topic_min": ON_TOPIC_MIN, "on_topic_first": ON_TOPIC_FIRST, "targets": {k: v["target"] for k, v in LEVELS.items()},
        "docs": [[d["id"], d["title"], d["url"], d["snippet"], round(d["difficulty"], 4), d["level"],
                  d["words"], d["topic"], d["source"]] for d in docs],
        "dl": ix.doc_len,
        "terms": terms,
    }
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    path = WEB_DATA / f"{lang}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path


def main(langs):
    ll = LinguaLadder()
    total = 0
    for lang in langs:
        p = export_lang(ll, lang)
        size = p.stat().st_size
        total += size
        print(f"{lang}: {size / 1e6:.2f} MB -> {p}")
    print(f"total {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_LANGS)
