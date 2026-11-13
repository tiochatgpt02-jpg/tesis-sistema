"""Prepared practices shared by a class; students never invoke an LLM."""
import hashlib
import json
from copy import deepcopy
from config import Config

_prepared = {}


def fingerprint(text, grade):
    return hashlib.sha256(f'{grade}:{text}'.encode()).hexdigest()


def save_practice(scope, text, grade, payload):
    if not payload.get('questions'):
        return
    stamp = fingerprint(text, grade)
    if Config.USE_MOCK_DATA:
        _prepared[scope] = {'fingerprint': stamp, 'payload': deepcopy(payload)}
        return
    from services.db_service import get_connection
    with get_connection() as conn:
        conn.execute('INSERT INTO prepared_practices (scope,fingerprint,payload) VALUES (%s,%s,%s::jsonb) '
                     'ON CONFLICT (scope) DO UPDATE SET fingerprint=EXCLUDED.fingerprint,payload=EXCLUDED.payload,created_at=CURRENT_TIMESTAMP',
                     (scope,stamp,json.dumps(payload,ensure_ascii=False)))


def get_practice(scope, text, title, grade):
    if Config.USE_MOCK_DATA:
        row = _prepared.get(scope)
    else:
        from services.db_service import get_connection
        with get_connection() as conn:
            row = conn.execute('SELECT fingerprint,payload FROM prepared_practices WHERE scope=%s',(scope,)).fetchone()
    if row and row['fingerprint'] == fingerprint(text,grade):
        return deepcopy(row['payload'])
    # Previously published materials can be practiced immediately even when the
    # provider is unavailable. These questions are deterministic and labelled.
    from services.ai_service import _grounded_fallback_from_text
    questions, activities = _grounded_fallback_from_text(text,title)
    payload = {'success': True, 'questions': questions, 'activities': activities, 'source': 'fallback'}
    save_practice(scope,text,grade,payload)
    return payload
