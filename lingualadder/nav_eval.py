"""Navigational queries: does the article named exactly like the query come first? (en and es, 3 targets)

Queries are the 304 topic labels in each language (the same chips the apps show). A query counts when the corpus
has at least one article whose title equals the label (accents and case ignored). Reported: share of those queries
whose rank-1 result is such an article, share with one in the top 3, and the level fit of the top 10 (share within
0.15 of the target) so the cost of a title bonus is visible.

python -m lingualadder.nav_eval [bonus ...]   -> data/nav_eval.json
"""
import json
import sys
import unicodedata

from .config import DATA_DIR, LEVELS
from .recommend import topic_labels
from .search import LinguaLadder


def norm(s):
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode().strip()


def run(ll, bonus):
    res = {}
    for lang in ("en", "es"):
        docs = ll.docs[lang]
        labels = topic_labels(docs, lang)
        bytitle = {}
        for d in docs:
            bytitle.setdefault(norm(d["title"]), set()).add(d["id"])
        qs = [labels.get(t, t) for t in sorted({d["topic"] for d in docs if d.get("topic")})]
        qs = [q for q in qs if norm(q) in bytitle]
        res[lang] = {"queries": len(qs)}
        for level, cfg in LEVELS.items():
            r1 = r3 = 0
            fit = []
            for q in qs:
                ids = bytitle[norm(q)]
                top = ll.search(lang, q, cfg["target"], k=10, title_bonus=bonus)
                pos = [i for i, x in enumerate(top) if x["id"] in ids]
                r1 += bool(pos and pos[0] == 0)
                r3 += bool(pos and pos[0] < 3)
                fit.append(sum(abs(x["difficulty"] - cfg["target"]) <= 0.15 for x in top) / max(len(top), 1))
            res[lang][level] = {"rank1": round(r1 / len(qs), 3), "top3": round(r3 / len(qs), 3),
                                "level_match": round(sum(fit) / len(fit), 3)}
    return res


def main():
    bonuses = [float(x) for x in sys.argv[1:]] or [0.0, 0.1, 0.2, 0.3, 0.5]
    ll = LinguaLadder()
    out = {}
    for b in bonuses:
        out[str(b)] = run(ll, b)
        for lang in ("en", "es"):
            r = out[str(b)][lang]
            print(f"bonus {b}: {lang} n={r['queries']} " + " | ".join(
                f"{lv[:3]} r1 {r[lv]['rank1']} top3 {r[lv]['top3']} fit {r[lv]['level_match']}" for lv in LEVELS), flush=True)
    (DATA_DIR / "nav_eval.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
