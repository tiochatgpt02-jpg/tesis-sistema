import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Config
from services import db_service


class PostgreSqlConnectionTests(unittest.TestCase):
    def test_get_connection_uses_postgres_configuration(self):
        with patch('services.db_service.psycopg.connect') as connect:
            connect.return_value = MagicMock()
            with patch.object(Config, 'USE_MOCK_DATA', False):
                db_service.get_connection()
        kwargs = connect.call_args.kwargs
        self.assertEqual(kwargs['host'], Config.POSTGRES_HOST)
        self.assertEqual(kwargs['port'], Config.POSTGRES_PORT)
        self.assertEqual(kwargs['dbname'], Config.POSTGRES_DB)

    def test_insert_uses_returning_identity(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {'id': 42}
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connection.cursor.return_value = cursor
        with patch('services.db_service.get_connection', return_value=connection):
            inserted = db_service._execute('INSERT INTO topics (title, grade) VALUES (%s, %s)', ('Tema', 5))
        self.assertEqual(inserted, 42)
        self.assertIn('RETURNING id', cursor.execute.call_args.args[0])


class DbServiceContractTests(unittest.TestCase):
    def test_fetch_topics_for_grade_respects_publication_and_section_in_mock(self):
        from services import mock_data
        topics = [
            {'id': 1, 'title': 'Visible', 'grade': 5, 'status': 'Publicado'},
            {'id': 2, 'title': 'Privado', 'grade': 5, 'status': 'Privado'},
            {'id': 3, 'title': 'Para B', 'grade': 5, 'status': 'Publicado', 'section': 'B'},
        ]
        with patch.object(Config, 'USE_MOCK_DATA', True), patch.dict(mock_data.MOCK_TOPICS, {5: topics}):
            self.assertEqual([item['id'] for item in db_service.fetch_topics_for_grade(5)], [1])
            self.assertEqual([item['id'] for item in db_service.fetch_topics_for_grade(5, 'A')], [1])
            self.assertEqual([item['id'] for item in db_service.fetch_topics_for_grade(5, ' b ')], [1, 3])


if __name__ == '__main__':
    unittest.main()
