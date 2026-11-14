"""Reordered-title queries: reverse the words of multi-word article titles; is that article rank 1? (en, es)
python -m lingualadder.reorder_eval"""
import json, re
from .config import DATA_DIR, LEVELS
from .search import LinguaLadder
from . import search as S

def run(ll):
    out = {}
    for lang in ("en", "es"):
        docs = [d for d in ll.docs[lang] if "(" not in d["title"] and len(d["title"].split()) in (2, 3)
                and "disambig" not in d["title"].lower()][::12][:250]
        res = {"queries": len(docs)}
        for lv, cfg in LEVELS.items():
            r1 = 0
            for d in docs:
                q = " ".join(reversed(d["title"].split()))
                top = ll.search(lang, q, cfg["target"], k=10)
                r1 += bool(top and top[0]["title"] == d["title"])
            res[lv] = round(r1 / len(docs), 3)
        out[lang] = res
    return out

if __name__ == "__main__":
    ll = LinguaLadder(); r = {}
    for v in (0.0, 0.5):
        S.REORDER_MATCH = v; r[str(v)] = run(ll); print(v, r[str(v)], flush=True)
    (DATA_DIR / "reorder_eval.json").write_text(json.dumps(r, indent=1))
