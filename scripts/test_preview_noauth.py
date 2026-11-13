import os
os.environ['USE_MOCK_DATA'] = 'true'

from app import app

with app.test_client() as client:
    resp = client.post('/teacher/api/generate-preview', json={'topic': 'paint', 'grade': 5})
    print('STATUS', resp.status_code)
    print(resp.get_json())
