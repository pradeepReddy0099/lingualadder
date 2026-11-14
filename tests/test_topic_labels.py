import json
from lingualadder.config import DATA_DIR


def test_spanish_topic_labels_cover_every_topic():
    labels = json.loads((DATA_DIR / "topic_labels_es.json").read_text(encoding="utf-8"))
    assert len(labels) >= 300
    assert all(v.strip() and "(" not in v for v in labels.values())
    assert labels["Ship"] == "Barco" and labels["Mexico City"] == "Ciudad de México"
