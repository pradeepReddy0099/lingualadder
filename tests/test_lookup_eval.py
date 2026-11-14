import numpy as np
from lingualadder.search import LinguaLadder
from lingualadder.evaluate import build_queries
from lingualadder.vocab import ranked_words
from lingualadder import lookup_eval as L

ENG = LinguaLadder()


def test_session_shapes_and_hard_nudge_lowers_target_en_es():
    for lang in ("en", "es"):
        qs = build_queries(ENG)[lang]
        ranked = ranked_words(ENG.docs[lang], lang)
        fixed = L.session(ENG, lang, qs, "beginner", "advanced", "fixed", ranked, 0)
        hard = L.session(ENG, lang, qs, "beginner", "advanced", "hard", ranked, 0)
        assert fixed["target_end"] == 0.8            # no nudge without lookups
        assert hard["target_end"] < 0.8              # a beginner on the advanced setting is nudged down
        for r in (fixed, hard):
            assert 0 <= r["cov_all"] <= 1 and 0 <= r["ndcg_all"] <= 1
