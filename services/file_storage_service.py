"""Small demonstration uploads persisted in PostgreSQL on ephemeral hosting."""
from config import Config


def store_bytes(path, content):
    if len(content) > 20 * 1024 * 1024:
        raise ValueError('El archivo supera 20 MB.')
    if not Config.DATABASE_URL or Config.USE_MOCK_DATA:
        return
    from services.db_service import get_connection
    with get_connection() as conn:
        conn.execute('INSERT INTO stored_files (path,content) VALUES (%s,%s) '
                     'ON CONFLICT(path) DO UPDATE SET content=EXCLUDED.content', (path, content))


def read_bytes(path):
    if not Config.DATABASE_URL or Config.USE_MOCK_DATA:
        return None
    from services.db_service import get_connection
    with get_connection() as conn:
        row = conn.execute('SELECT content FROM stored_files WHERE path=%s', (path,)).fetchone()
    return bytes(row['content']) if row else None


def delete_bytes(path):
    if not Config.DATABASE_URL or Config.USE_MOCK_DATA:
        return
    from services.db_service import get_connection
    with get_connection() as conn:
        conn.execute('DELETE FROM stored_files WHERE path=%s', (path,))
