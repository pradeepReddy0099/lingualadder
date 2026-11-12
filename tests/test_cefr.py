from lingualadder.search import cefr_label

def test_cefr_bounds():
    assert cefr_label(0) == "A1" and cefr_label(1) == "C2" and cefr_label(0.5) == "A2"
