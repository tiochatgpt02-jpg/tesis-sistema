from app import app
from config import Config

Config.USE_MOCK_DATA = False

client = app.test_client()
resp = client.post('/login', data={'username': 'profesor1', 'password': 'Admin123'}, follow_redirects=False)
print('login_status', resp.status_code)
print('location', resp.headers.get('Location'))
if resp.status_code == 302:
    with client.session_transaction() as sess:
        print('session', dict(sess))
    teacher_resp = client.get(resp.headers['Location'], follow_redirects=False)
    print('teacher_status', teacher_resp.status_code)
    print('teacher_body_start', teacher_resp.get_data(as_text=True)[:800])
