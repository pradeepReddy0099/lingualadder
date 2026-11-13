import json, os

def test_coverage_report_en_es():
    p = os.path.join(os.path.dirname(__file__), "..", "data", "coverage.json")
    d = json.load(open(p))
    for lang in ("en", "es"):
        r = d[lang]
        assert r["topics"] == 304
        assert r["complete"] + len(r["gaps"]) == r["topics"]
        assert r["complete"] >= 290
