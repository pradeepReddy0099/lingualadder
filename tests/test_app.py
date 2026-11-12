from app import app
def test_home():
    c=app.test_client(); assert c.get('/').status_code==200
def test_search():
    c=app.test_client(); c.post('/',data={'target':'en','native':'te','level':'beginner'})
    r=c.get('/search?q=volcano'); assert r.status_code==200
