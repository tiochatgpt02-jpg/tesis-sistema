#!/usr/bin/env python3
"""Migración de una sola vía desde MySQL histórico hacia PostgreSQL.

No es un fallback de la aplicación. Requiere mysql-connector-python únicamente
durante la migración y conserva IDs para que las relaciones sigan siendo válidas.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

import psycopg
from psycopg import sql
from psycopg.types.json import Json
from werkzeug.security import generate_password_hash
from config import Config

BOOLEAN_COLUMNS = {'is_active', 'approved', 'is_correct', 'is_read', 'is_at_risk'}
# Referencias opcionales que ya eran huérfanas en el MySQL histórico. Se conserva
# el registro y se elimina solamente la referencia inválida.
ORPHANABLE_REFERENCE_COLUMNS = {('ai_generated_games', 'created_by')}

# Padres antes que hijos: MySQL no garantiza que SHOW TABLES respete las FK.
TABLE_ORDER = (
    'students', 'topics', 'users', 'student_progress', 'ai_recommendations',
    'grades', 'student_notes', 'learning_materials', 'material_reviews',
    'topic_activities', 'topic_games', 'topic_evaluations', 'assessment',
    'questions', 'student_assessment_attempts', 'student_game_attempts',
    'topic_presentations', 'ai_generated_games', 'teacher_topics',
    'teacher_messages', 'student_submissions', 'alerts',
    'student_academic_outcomes', 'student_results', 'teacher_recommendations',
)


def mysql_connection():
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError(
            'Instala mysql-connector-python solo para esta migración: '
            'python -m pip install mysql-connector-python'
        ) from exc
    required = ('MYSQL_SOURCE_HOST', 'MYSQL_SOURCE_USER', 'MYSQL_SOURCE_PASSWORD', 'MYSQL_SOURCE_DB')
    missing = [key for key in required if not __import__('os').getenv(key)]
    if missing:
        raise RuntimeError(f'Faltan variables de origen: {", ".join(missing)}')
    return mysql.connector.connect(
        host=__import__('os').environ['MYSQL_SOURCE_HOST'],
        port=int(__import__('os').getenv('MYSQL_SOURCE_PORT', '3306')),
        user=__import__('os').environ['MYSQL_SOURCE_USER'],
        password=__import__('os').environ['MYSQL_SOURCE_PASSWORD'],
        database=__import__('os').environ['MYSQL_SOURCE_DB'],
    )


def postgres_connection():
    return psycopg.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT, user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD, dbname=Config.POSTGRES_DB,
    )


def convert_value(table, column, value):
    if value is None:
        return None
    if (table, column) in ORPHANABLE_REFERENCE_COLUMNS:
        return None
    if column in {'options', 'questions', 'answers', 'content_json', 'ai_payload'}:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return Json(value)
        return Json(value)
    if column == 'password_hash' and isinstance(value, str) and not value.startswith(('scrypt:', 'pbkdf2:', 'argon2:')):
        return generate_password_hash(value)
    if column in BOOLEAN_COLUMNS:
        return bool(value)
    return value


def list_source_tables(conn):
    cursor = conn.cursor()
    cursor.execute('SHOW TABLES')
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def target_tables(conn):
    return {
        row[0] for row in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall()
    }


def migrate_table(source, target, table):
    read = source.cursor(dictionary=True)
    read.execute(f'SELECT * FROM `{table}`')
    rows = read.fetchall()
    read.close()
    if not rows:
        return 0
    columns = list(rows[0])
    statement = sql.SQL('INSERT INTO {} ({}) OVERRIDING SYSTEM VALUE VALUES ({}) ON CONFLICT DO NOTHING').format(
        sql.Identifier(table), sql.SQL(', ').join(map(sql.Identifier, columns)),
        sql.SQL(', ').join(sql.Placeholder() for _ in columns),
    )
    with target.cursor() as cursor:
        for row in rows:
            cursor.execute(statement, [convert_value(table, column, row[column]) for column in columns])
    return len(rows)


def reset_sequences(conn, tables):
    for table in tables:
        result = conn.execute(
            'SELECT pg_get_serial_sequence(%s, %s)', (table, 'id')
        ).fetchone()
        if result and result[0]:
            maximum = conn.execute(
                sql.SQL('SELECT COALESCE(MAX(id), 1) FROM {}').format(sql.Identifier(table))
            ).fetchone()[0]
            conn.execute('SELECT setval(%s, %s, true)', (result[0], maximum))


def main():
    source = mysql_connection()
    target = postgres_connection()
    try:
        available = target_tables(target)
        source_tables = set(list_source_tables(source))
        tables = [table for table in TABLE_ORDER if table in source_tables and table in available]
        tables.extend(sorted((source_tables & available) - set(tables)))
        counts = {table: migrate_table(source, target, table) for table in tables}
        reset_sequences(target, tables)
        target.commit()
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()
    print(json.dumps({'migrated_tables': counts, 'total_rows_read': sum(counts.values())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
