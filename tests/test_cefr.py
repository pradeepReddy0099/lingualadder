import json
from pathlib import Path

from lingualadder.search import CEFR_CUTS, CEFR_NAMES, cefr_label


def test_cefr_bounds_and_monotone():
    for lang, cuts in CEFR_CUTS.items():
        assert len(cuts) == 5 and cuts == sorted(cuts)
        labels = [cefr_label(x / 100, lang) for x in range(101)]
        assert labels[0] == "A1" and labels[-1] == "C2"
        assert [CEFR_NAMES.index(l) for l in labels] == sorted(CEFR_NAMES.index(l) for l in labels)
    assert cefr_label(0.5, "en") == "B2" and cefr_label(0.5, "es") == "C1"


def test_bands_are_per_language_and_default_en():
    assert cefr_label(0.2) == cefr_label(0.2, "en") == "B1"
    assert cefr_label(0.2, "es") == "B2"
    assert cefr_label(0.2, "xx") == "B1"


def test_external_validation_report_en_and_es():
    p = Path(__file__).resolve().parent.parent / "data" / "cefr_validation.json"
    r = json.loads(p.read_text())
    en, es = r["languages"]["en"], r["languages"]["es"]
    assert en["cuts_shipped"] == CEFR_CUTS["en"] and es["cuts_shipped"] == CEFR_CUTS["es"]
    assert en["heldout_mean_of_10_splits"]["quantile"]["within1"] > 0.9
    for lang in (en, es):  # new bands beat the old corpus-quantile bands on held-out external texts
        h = lang["heldout_mean_of_10_splits"]
        assert h["quantile"]["exact"] > h["old"]["exact"] and h["quantile"]["within1"] > h["old"]["within1"]
