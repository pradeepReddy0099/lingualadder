"""Write web/parity_expected.json: Python's top-10 for sample queries, to check the JS port (node web/parity_test.js)."""
import json

from .config import DATA_DIR, LEVELS
from .search import LinguaLadder

CASES = [("en", "volcano eruption"), ("en", "how do airplanes fly"), ("en", "Albert Einstein relativity"),
         ("es", "frida kahlo pintora"), ("es", "sistema solar planetas")]


def main():
    ll = LinguaLadder()
    out = []
    for lang, q in CASES:
        for lvl, v in LEVELS.items():
            res = ll.search(lang, q, v["target"], k=10)
            out.append({"lang": lang, "query": q, "level": lvl, "target": v["target"],
                        "ids": [r["id"] for r in res], "scores": [r["score"] for r in res]})
    p = DATA_DIR.parent / "web" / "parity_expected.json"
    p.write_text(json.dumps(out, ensure_ascii=False))
    print(len(out), "cases ->", p)


if __name__ == "__main__":
    main()
