import os
os.environ['USE_MOCK_DATA'] = 'true'

from app import app

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user'] = 'profesor1'
        sess['is_authenticated'] = True
        sess['user_role'] = 'teacher'
    resp = client.post('/teacher/api/generate-preview', json={'topic': 'paint', 'grade': 5})
    print('STATUS', resp.status_code)
    print(resp.get_json())
