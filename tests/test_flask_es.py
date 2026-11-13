from app import app


def test_spanish_search_ok():
    c = app.test_client()
    c.post('/', data={'target': 'es', 'native': 'en', 'level': 'beginner'})
    r = c.get('/search?q=volcan')
    assert r.status_code == 200
