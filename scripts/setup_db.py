#!/usr/bin/env python3
"""Crea e inicializa la base oficial PostgreSQL."""
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

import psycopg
from psycopg import sql
from config import Config


def connection_kwargs(database):
    return {
        'host': Config.POSTGRES_HOST,
        'port': Config.POSTGRES_PORT,
        'user': Config.POSTGRES_USER,
        'password': Config.POSTGRES_PASSWORD,
        'dbname': database,
    }


def run_file(conn, path):
    conn.execute(path.read_text(encoding='utf-8'))
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description='Aplicar esquema y migraciones sin borrar datos.')
    parser.add_argument('--seed', action='store_true', help='Importar explícitamente el padrón existente del repositorio.')
    options = parser.parse_args()
    schema = ROOT / 'sql' / 'postgresql' / 'ddl.sql'
    migrations = sorted((ROOT / 'sql' / 'migrations' / 'postgresql').glob('*.sql'))
    seed = ROOT / 'sql' / 'postgresql' / 'seed.sql'
    if options.seed and not seed.is_file():
        raise SystemExit('El padrón real es local y no se distribuye en Git. Para cuentas ficticias usa scripts/seed_demo.py.')
    try:
        if not Config.DATABASE_URL:
            with psycopg.connect(**connection_kwargs('postgres'), autocommit=True) as admin:
                exists = admin.execute('SELECT 1 FROM pg_database WHERE datname = %s', (Config.POSTGRES_DB,)).fetchone()
                if not exists:
                    admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(Config.POSTGRES_DB)))
        connection = psycopg.connect(Config.DATABASE_URL) if Config.DATABASE_URL else psycopg.connect(**connection_kwargs(Config.POSTGRES_DB))
        with connection as conn:
            run_file(conn, schema)
            for migration in migrations:
                run_file(conn, migration)
            if options.seed:
                run_file(conn, seed)
    except psycopg.Error as exc:
        print(f'Error PostgreSQL: {exc}')
        print('Verifica POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER y POSTGRES_PASSWORD en .env.')
        raise SystemExit(1)
    print('PostgreSQL listo; datos existentes conservados.')
    print(f'Migraciones aplicadas: {len(migrations)}')
    print('Padrón importado.' if options.seed else 'Sin importar padrón. Para cuentas ficticias: python scripts/seed_demo.py')


if __name__ == '__main__':
    main()
