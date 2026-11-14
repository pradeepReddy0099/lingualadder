"""Display-only split of the crowded top CEFR band (python -m lingualadder.cefr_split).

The validated cuts (search.CEFR_CUTS) put 67% of English articles in C2 and 79% of Spanish ones in C1.
For display, the crowded band is halved at its corpus median: the upper half gets a "+" (e.g. C2+).
Filtering and placement keep using the validated bands; "+" only adds detail inside one band.
Prints the median to paste into search.CEFR_SPLIT and writes data/cefr_split.json.
"""
import json
from collections import Counter
from .config import DATA_DIR
from .search import CEFR_CUTS, CEFR_NAMES, CEFR_SPLIT, cefr_label, cefr_display

def main():
    docs = [json.loads(l) for l in open(DATA_DIR / "corpus.jsonl", encoding="utf-8")]
    out = {}
    for lang in ("en", "es"):
        d = sorted(r["difficulty"] for r in docs if r["lang"] == lang)
        band = CEFR_SPLIT[lang][0]
        lo = CEFR_CUTS[lang][CEFR_NAMES.index(band) - 1]
        hi = CEFR_CUTS[lang][CEFR_NAMES.index(band)] if band != "C2" else 9
        inb = [x for x in d if lo <= x < hi]
        median = round(inb[len(inb) // 2], 4)
        before = Counter(cefr_label(x, lang) for x in d)
        after = Counter(cefr_display(x, lang) for x in d)
        out[lang] = {"band": band, "median_in_band": median, "shipped_median": CEFR_SPLIT[lang][1], "n": len(d),
                     "before": {k: before.get(k, 0) for k in CEFR_NAMES},
                     "after": {k: after[k] for k in sorted(after)}}
        print(lang, out[lang])
    json.dump(out, open(DATA_DIR / "cefr_split.json", "w"), indent=1)

if __name__ == "__main__":
    main()
