import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "data" / "cefr_es_exp.json"


def test_es_cefr_experiment_report_is_complete():
    r = json.load(open(P))
    assert r["n_caes"] >= 2000 and r["n_kwiziq"] > 100
    for k in ("current_score_spearman", "band_transfer_cuts_from_caes", "articles"):
        assert k in r
    # the production score must still separate easy from regular Spanish articles better than chance
    assert r["articles"]["production_score"]["auc_wiki_above_vikidia"] > 0.8
