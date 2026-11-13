"""Run locally against the cloud DATABASE_URL before the demonstration."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from services.db_service import _query
from services.file_storage_service import store_bytes
from config import Config


def main():
    if not Config.DATABASE_URL or Config.USE_MOCK_DATA:
        raise SystemExit('Requiere DATABASE_URL del destino y USE_MOCK_DATA=false.')
    root = Path(__file__).resolve().parent.parent
    rows = _query('SELECT file_path FROM topic_presentations UNION SELECT file_path FROM student_submissions')
    saved = missing = 0
    for row in rows:
        key = row.get('file_path') or ''
        relative = key.replace('\\','/').lstrip('/')
        if relative.startswith('presentations/'):
            path = (root/'instance'/'uploads'/relative).resolve()
        elif relative.startswith('static/uploads/'):
            path = (root/relative).resolve()
        else:
            missing += 1
            continue
        if not path.is_relative_to(root):
            missing += 1
            continue
        if path.is_file():
            store_bytes(key if relative.startswith('static/') else relative,path.read_bytes())
            saved += 1
        else:
            missing += 1
    print(f'Archivos guardados: {saved}; archivos pendientes/no encontrados: {missing}.')


if __name__ == '__main__':
    main()
