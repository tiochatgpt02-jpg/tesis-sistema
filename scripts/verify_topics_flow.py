import os
os.environ['USE_MOCK_DATA'] = 'true'
from app import app

client = app.test_client()
resp = client.post('/teacher/api/generate-preview', json={'topic': 'fracciones', 'grade': 5})
print('STATUS', resp.status_code)
print(resp.get_json())
