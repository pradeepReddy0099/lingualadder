from lingualadder.search import adapt_target


def test_adapt_target():
    assert abs(adapt_target(0.5, ["too_easy", "too_easy"]) - 0.6) < 1e-9
    assert adapt_target(0.02, ["too_hard"]) == 0.0
    assert adapt_target(0.5, []) == 0.5
