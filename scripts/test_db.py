#!/usr/bin/env python3
"""Prueba la conexión PostgreSQL con las credenciales del archivo .env."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from config import Config
from services.db_service import test_connection, fetch_students, fetch_user_by_username


def main():
    print('Configuración:')
    print(f'  Host:     {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}')
    print(f'  Usuario:  {Config.POSTGRES_USER}')
    print(f'  Base:     {Config.POSTGRES_DB}')
    print(f'  Mock:     {Config.USE_MOCK_DATA}')
    print()

    ok, msg = test_connection()
    if not ok:
        print(f'FALLÓ: {msg}')
        print('\nPasos:')
        print('  1. Edita .env y pon tu contraseña en POSTGRES_PASSWORD')
        print('  2. Ejecuta: python scripts/setup_db.py')
        sys.exit(1)

    print(f'OK: {msg}')
    students = fetch_students()
    print(f'  Estudiantes en BD: {len(students)}')
    user = fetch_user_by_username('profesor1')
    print(f'  Usuario profesor1: {"encontrado" if user else "NO encontrado"}')
    print('\nConexión real lista. Ejecuta: python app.py')


if __name__ == '__main__':
    main()
