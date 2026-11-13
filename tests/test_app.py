from app import app
def test_home():
    c=app.test_client(); assert c.get('/').status_code==200
def test_search():
    c=app.test_client(); c.post('/',data={'target':'en','native':'te','level':'beginner'})
    r=c.get('/search?q=volcano'); assert r.status_code==200


def test_404_page():
    from app import app
    r = app.test_client().get('/nope-nothing')
    assert r.status_code == 404 and b'Back to LinguaLadder' in r.data


def test_feedback_moves_target_both_languages():
    from app import app
    for lang in ('en', 'es'):
        c = app.test_client()
        c.post('/', data={'target': lang, 'native': 'te', 'level': 'intermediate'})
        up = c.post('/api/feedback', json={'verdict': 'too_hard'}).get_json()
        down = c.post('/api/feedback', json={'verdict': 'too_easy'}).get_json()
        assert up['offset'] < 0 < down['offset'] - up['offset']
        assert c.post('/api/feedback', json={'verdict': 'bad'}).status_code == 400
