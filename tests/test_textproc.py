from lingualadder import textproc as t

def test_words_en():
    assert t.words("Hello, world!", "en")[:2] == ["Hello", "world"]

def test_cjk_flag():
    assert t.is_cjk("ja") and not t.is_cjk("en")

def test_index_tokens_nonempty():
    assert len(t.index_tokens("Volcanoes erupt molten rock.", "en")) >= 3

def test_sentences_split():
    assert len(t.sentences("One. Two. Three.")) == 3

def test_strip_headings():
    assert "Heading" not in t.strip_headings("== Heading ==\nbody text")
