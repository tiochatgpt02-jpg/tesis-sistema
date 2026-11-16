import csv
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import psycopg
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.grade_service import (
    normalize_to_scale_20,
    score_20_to_percentage_100,
    percentage_100_to_score_20,
)
from services import db_service, mock_data
from services.ml.feature_service import FeatureService
from services.ml.model_registry import ModelRegistry, get_model_registry
from services.ml.prediction_service import RiskPredictionService, get_risk_prediction_service
from services.ml_service import build_prediction_payload, predict_student_performance
from ml.scripts.import_historical_data import import_csv
from ml.scripts.build_dataset import build_training_dataset
from ml.scripts.train import load_dataset, split_dataset
from config import Config


class TestGradeScaleConversions(unittest.TestCase):
    """Pruebas de conversion matematica estricta entre escala 0-20 y 0-100%."""

    def test_score_20_to_percentage_100(self):
        self.assertEqual(score_20_to_percentage_100(0), 0.0)
        self.assertEqual(score_20_to_percentage_100(10), 50.0)
        self.assertEqual(score_20_to_percentage_100(14), 70.0)
        self.assertEqual(score_20_to_percentage_100(20), 100.0)
        # Clamping
        self.assertEqual(score_20_to_percentage_100(-5), 0.0)
        self.assertEqual(score_20_to_percentage_100(25), 100.0)

    def test_percentage_100_to_score_20(self):
        self.assertEqual(percentage_100_to_score_20(0), 0.0)
        self.assertEqual(percentage_100_to_score_20(50), 10.0)
        self.assertEqual(percentage_100_to_score_20(70), 14.0)
        self.assertEqual(percentage_100_to_score_20(100), 20.0)
        # Clamping
        self.assertEqual(percentage_100_to_score_20(-10), 0.0)
        self.assertEqual(percentage_100_to_score_20(120), 20.0)

    def test_normalize_to_scale_20(self):
        self.assertEqual(normalize_to_scale_20(15), 15.0)
        self.assertEqual(normalize_to_scale_20(80), 16.0)
        self.assertEqual(normalize_to_scale_20('invalid'), 0.0)
        self.assertEqual(normalize_to_scale_20(None), 0.0)


class TestStudentNotesRecording(unittest.TestCase):
    """Verificacion de que student_notes registra score en 0-20 y percentage en 0-100%."""

    def setUp(self):
        db_service._use_mock = lambda: True
        from services import mock_data
        mock_data.MOCK_STUDENT_NOTES.clear()

    def test_record_student_result_normalizes_scales(self):
        from services import mock_data
        # Caso 1: se proporciona score en escala 0-20
        db_service.record_student_result(
            student_id=1, topic_id=1, activity_type='evaluaciones',
            item_type='evaluation', score=16.0, correct_answers=4, wrong_answers=1
        )
        saved = mock_data.MOCK_STUDENT_NOTES[-1]
        self.assertEqual(saved['score'], 16.0)
        self.assertEqual(saved['percentage'], 80.0)

        # Caso 2: se proporciona porcentaje 100%
        db_service.record_student_result(
            student_id=1, topic_id=1, activity_type='actividades',
            item_type='activity', score=None, percentage=75.0, correct_answers=3, wrong_answers=1
        )
        saved = mock_data.MOCK_STUDENT_NOTES[-1]
        self.assertEqual(saved['score'], 15.0)
        self.assertEqual(saved['percentage'], 75.0)


class TestFeatureExtractionTemporalIsolation(unittest.TestCase):
    """Verificacion de no-leakage temporal con cutoff_date y exclusion de datos personales."""

    def test_cutoff_date_filters_future_events(self):
        # 3 registros: 2 antes del cutoff y 1 posterior
        notes = [
            {'activity_type': 'actividades', 'score': 14.0, 'correct_answers': 3, 'wrong_answers': 1, 'time_spent_seconds': 60, 'created_at': '2024-03-01T10:00:00'},
            {'activity_type': 'evaluaciones', 'score': 18.0, 'correct_answers': 5, 'wrong_answers': 0, 'time_spent_seconds': 120, 'created_at': '2024-04-01T10:00:00'},
            {'activity_type': 'evaluaciones', 'score': 6.0, 'correct_answers': 1, 'wrong_answers': 4, 'time_spent_seconds': 30, 'created_at': '2024-05-15T10:00:00'},
        ]

        # Con corte al 15 de abril de 2024, la nota del 15 de mayo NO debe incluirse
        features = FeatureService.extract_features_from_records(notes=notes, cutoff_date='2024-04-15')

        self.assertEqual(features['total_attempts'], 2)
        # Promedio de 14.0 y 18.0 es 16.0
        self.assertEqual(features['average_score'], 16.0)
        self.assertEqual(features['min_score'], 14.0)
        self.assertEqual(features['max_score'], 18.0)

    def test_features_contain_no_personal_identifiable_information(self):
        notes = [{'activity_type': 'actividades', 'score': 15.0, 'created_at': '2024-03-01T10:00:00'}]
        features = FeatureService.extract_features_from_records(notes=notes)
        for personal_key in ['student_id', 'student_name', 'first_name', 'last_name', 'dni', 'email']:
            self.assertNotIn(personal_key, features)


class TestModelInferenceStatus(unittest.TestCase):
    """Verificacion de que la ausencia de modelo devuelve explicitamente MODEL_NOT_AVAILABLE."""

    def test_prediction_returns_model_not_available_when_untrained(self):
        registry = get_model_registry()
        orig_model = registry._cached_model
        orig_meta = registry._cached_metadata
        try:
            registry._cached_model = None
            registry._cached_metadata = {'status': 'MODEL_NOT_AVAILABLE'}
            with patch.object(registry, 'is_available', return_value=False):
                service = RiskPredictionService(registry=registry)
                self.assertFalse(service.is_available())

                res = service.predict_for_student(student_id=999)
                self.assertFalse(res['success'])
                self.assertEqual(res['code'], 'MODEL_NOT_AVAILABLE')
                self.assertEqual(res['risk_level'], 'No disponible')

                payload = build_prediction_payload(student_id=999)
                self.assertFalse(payload['success'])
                self.assertEqual(payload['code'], 'MODEL_NOT_AVAILABLE')
        finally:
            registry._cached_model = orig_model
            registry._cached_metadata = orig_meta

    def test_prediction_with_loaded_mock_model(self):
        registry = get_model_registry()
        dummy_model = MagicMock()
        dummy_model.classes_ = np.array([0, 1])
        dummy_model.predict.return_value = [1]
        dummy_model.predict_proba.return_value = [[0.20, 0.80]]

        orig_model = registry._cached_model
        orig_meta = registry._cached_metadata
        try:
            registry._cached_model = dummy_model
            registry._cached_metadata = {'status': 'AVAILABLE', 'version': 'test_v1', 'features': registry.DEFAULT_FEATURE_NAMES}
            service = RiskPredictionService(registry=registry)
            self.assertTrue(service.is_available())

            dummy_features = {f: 10.0 for f in registry.DEFAULT_FEATURE_NAMES}
            res = service.predict_for_features(dummy_features)

            self.assertTrue(res['success'])
            self.assertEqual(res['risk_level'], 'Alto')
            self.assertEqual(res['risk_probability'], 0.80)
            self.assertEqual(res['predicted_class'], 1)
        finally:
            registry._cached_model = orig_model
            registry._cached_metadata = orig_meta

    def test_predict_student_performance_has_no_randomness(self):
        res1 = predict_student_performance(70.0, 'actividades')
        res2 = predict_student_performance(70.0, 'actividades')
        self.assertEqual(res1, res2)
        self.assertEqual(res1['level'], 'bueno')
        self.assertEqual(res1['score'], 70.0)


class TestDatabaseNoSilentMockFallback(unittest.TestCase):
    """Verificacion de que cuando USE_MOCK_DATA=False, los fallos de BD levantan error real."""

    def test_fetch_students_raises_on_db_error_when_mock_disabled(self):
        with patch.object(Config, 'USE_MOCK_DATA', False):
            with patch('services.db_service._use_mock', return_value=False):
                with patch('services.db_service.get_connection', side_effect=psycopg.Error('Connection refused')):
                    with self.assertRaises(psycopg.Error):
                        db_service.fetch_students()

    def test_fetch_user_by_username_does_not_return_mock_when_disabled(self):
        with patch.object(Config, 'USE_MOCK_DATA', False):
            with patch('services.db_service._use_mock', return_value=False):
                with patch('services.db_service.get_connection', side_effect=psycopg.Error('Connection refused')):
                    with self.assertRaises(psycopg.Error):
                        db_service.fetch_user_by_username('profesor1')


class TestHistoricalDataImporter(unittest.TestCase):
    """Verifica importación de historial con múltiples notas por estudiante y su outcome final."""

    def setUp(self):
        db_service._use_mock = lambda: True
        mock_data.MOCK_STUDENT_NOTES.clear()
        mock_data.MOCK_ACADEMIC_OUTCOMES.clear()

    def test_import_historical_csv_notes_and_outcomes(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp:
            writer = csv.writer(tmp)
            writer.writerow([
                'student_code', 'academic_year', 'period', 'subject',
                'event_date', 'activity_type', 'score', 'attendance_percentage',
                'final_score', 'final_status', 'is_at_risk'
            ])
            # Nota 1
            writer.writerow(['ALU-0099', '2024', 'B1', 'Computación', '2024-03-15', 'actividades', '14.0', '95.0', '', '', ''])
            # Nota 2
            writer.writerow(['ALU-0099', '2024', 'B1', 'Computación', '2024-04-10', 'evaluaciones', '16.0', '', '', '', ''])
            # Outcome final
            writer.writerow(['ALU-0099', '2024', 'B1', 'Computación', '', '', '', '92.0', '15.0', 'aprobado', '0'])
            tmp_path = Path(tmp.name)

        try:
            summary = import_csv(tmp_path)
            self.assertEqual(summary['valid'], 3)
            self.assertEqual(summary['notes_inserted'], 2)
            self.assertEqual(summary['outcomes_inserted'], 1)

            # Verificar que student_notes tiene los eventos con fechas y notas preservadas
            notes = [n for n in mock_data.MOCK_STUDENT_NOTES]
            self.assertEqual(len(notes), 2)
            self.assertEqual(notes[0]['score'], 14.0)
            self.assertEqual(notes[0]['activity_type'], 'actividades')
            self.assertEqual(notes[1]['score'], 16.0)
            self.assertEqual(notes[1]['activity_type'], 'evaluaciones')

            # Verificar que outcomes contiene el registro oficial
            outcomes = [o for o in mock_data.MOCK_ACADEMIC_OUTCOMES]
            self.assertEqual(len(outcomes), 1)
            self.assertEqual(outcomes[0]['final_score'], 15.0)
            self.assertEqual(outcomes[0]['is_at_risk'], 0)
            self.assertEqual(outcomes[0]['attendance_percentage'], 92.0)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestBuildDatasetCutoffAntiLeakage(unittest.TestCase):
    """Verifica que build_dataset.py genera features estrictamente con eventos <= cutoff_date."""

    def setUp(self):
        db_service._use_mock = lambda: True
        mock_data.MOCK_STUDENT_NOTES.clear()
        mock_data.MOCK_ACADEMIC_OUTCOMES.clear()

    def test_events_after_cutoff_do_not_leak_into_features(self):
        student_id = 77
        # Evento 1 (antes del corte)
        db_service.record_student_result(
            student_id=student_id, topic_id=None, activity_type='actividades',
            item_type='historical', score=18.0, created_at='2024-03-01 10:00:00'
        )
        # Evento 2 (antes del corte)
        db_service.record_student_result(
            student_id=student_id, topic_id=None, activity_type='evaluaciones',
            item_type='historical', score=16.0, created_at='2024-03-20 10:00:00'
        )
        # Evento 3 (POSTERIOR al corte)
        db_service.record_student_result(
            student_id=student_id, topic_id=None, activity_type='evaluaciones',
            item_type='historical', score=5.0, created_at='2024-05-15 10:00:00'
        )

        # Outcome oficial del periodo
        db_service.insert_academic_outcome(
            student_id=student_id, academic_year=2024, period='B1',
            final_score=13.0, is_at_risk=0
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Corte al 31 de marzo de 2024
            count = build_training_dataset(cutoff_date='2024-03-31', output_path=tmp_path)
            self.assertEqual(count, 1)

            with tmp_path.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            row = rows[0]

            # total_attempts debe ser 2 (el evento 3 de mayo fue estrictamente ignorado por fecha de corte)
            self.assertEqual(float(row['total_attempts']), 2.0)
            # average_score debe ser (18 + 16)/2 = 17.0 (no contaminado por la nota 5.0)
            self.assertEqual(float(row['average_score']), 17.0)
            self.assertEqual(float(row['min_score']), 16.0)
            self.assertEqual(float(row['max_score']), 18.0)
            self.assertEqual(int(row['target_risk']), 0)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestTrainTemporalSplitAndSecurity(unittest.TestCase):
    """Verifica el split temporal por año/periodo y la exclusión estricta de student_id de la matriz X."""

    def test_temporal_split_chronological_selection(self):
        metadata = [
            {'academic_period': '2023-B1', 'student_id': 1},
            {'academic_period': '2023-B1', 'student_id': 2},
            {'academic_period': '2023-B2', 'student_id': 3},
            {'academic_period': '2023-B2', 'student_id': 4},
            {'academic_period': '2024-B1', 'student_id': 5},
            {'academic_period': '2024-B1', 'student_id': 6},
        ]
        X = np.ones((6, 4))
        y = np.array([0, 1, 0, 1, 0, 1])
        groups = np.array([1, 2, 3, 4, 5, 6])

        # Caso 1: Temporal split automático (último periodo cronológico como test)
        train_idx, test_idx, strategy, test_per = split_dataset(
            X, y, groups, metadata, split_strategy='temporal'
        )
        self.assertEqual(strategy, 'temporal')
        self.assertEqual(test_per, '2024-B1')
        self.assertEqual(list(test_idx), [4, 5])
        self.assertEqual(list(train_idx), [0, 1, 2, 3])

        # Caso 2: Fallback automático cuando solo hay 1 periodo en el dataset
        single_period_meta = [{'academic_period': '2024-B1', 'student_id': i} for i in range(1, 7)]
        train_idx, test_idx, strategy, test_per = split_dataset(
            X, y, groups, single_period_meta, split_strategy='temporal'
        )
        self.assertEqual(strategy, 'group')
        self.assertIsNone(test_per)

    def test_feature_matrix_never_contains_student_id_or_code(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp:
            writer = csv.writer(tmp)
            writer.writerow([
                'student_id', 'student_code', 'academic_year', 'period', 'cutoff_date',
                'total_attempts', 'average_score', 'score_std', 'target_risk'
            ])
            for i in range(1, 7):
                writer.writerow([i, f'ALU-000{i}', '2024', 'B1', '2024-04-01', 5, 14.5, 1.2, i % 2])
            tmp_path = Path(tmp.name)

        try:
            X, y, groups, feature_cols, metadata = load_dataset(tmp_path)

            # Verificación explícita de que NINGÚN identificador entra a X
            self.assertNotIn('student_id', feature_cols)
            self.assertNotIn('student_code', feature_cols)
            self.assertNotIn('academic_year', feature_cols)
            self.assertNotIn('period', feature_cols)
            self.assertNotIn('cutoff_date', feature_cols)
            self.assertNotIn('target_risk', feature_cols)

            for col in feature_cols:
                self.assertNotIn('student', col.lower())
                self.assertNotIn('code', col.lower())
                self.assertNotIn('id', col.lower())

            self.assertEqual(feature_cols, ['total_attempts', 'average_score', 'score_std'])
            self.assertEqual(X.shape, (6, 3))
            self.assertEqual(len(groups), 6)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_train_and_select_best_model_saves_clean_metadata(self):
        from ml.scripts.train import train_and_select_best_model
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / 'test_dataset.csv'
            output_dir = Path(tmp_dir) / 'models'

            with csv_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'student_id', 'student_code', 'academic_year', 'period', 'cutoff_date',
                    'total_attempts', 'average_score', 'score_std', 'target_risk'
                ])
                # 8 students across 2 periods with both classes
                # Train period: 2023-B1 (4 students, both classes)
                writer.writerow([1, 'ALU-0001', '2023', 'B1', '2023-04-01', 6, 17.0, 1.0, 0])
                writer.writerow([2, 'ALU-0002', '2023', 'B1', '2023-04-01', 5, 15.0, 1.2, 0])
                writer.writerow([3, 'ALU-0003', '2023', 'B1', '2023-04-01', 2, 8.0, 0.5, 1])
                writer.writerow([4, 'ALU-0004', '2023', 'B1', '2023-04-01', 3, 7.5, 0.8, 1])
                # Test period: 2024-B1 (4 students, both classes)
                writer.writerow([5, 'ALU-0005', '2024', 'B1', '2024-04-01', 7, 18.0, 0.9, 0])
                writer.writerow([6, 'ALU-0006', '2024', 'B1', '2024-04-01', 6, 16.0, 1.1, 0])
                writer.writerow([7, 'ALU-0007', '2024', 'B1', '2024-04-01', 2, 9.0, 0.4, 1])
                writer.writerow([8, 'ALU-0008', '2024', 'B1', '2024-04-01', 1, 6.0, 0.0, 1])

            meta = train_and_select_best_model(
                dataset_path=csv_path,
                output_dir=output_dir,
                split_strategy='temporal',
            )

            self.assertEqual(meta['status'], 'MODEL_AVAILABLE')
            self.assertEqual(meta['split_strategy'], 'temporal')
            self.assertEqual(meta['temporal_test_period'], '2024-B1')
            self.assertIn('student_risk_pipeline.joblib', [p.name for p in output_dir.iterdir()])
            self.assertNotIn('student_id', meta['features'])
            self.assertNotIn('student_code', meta['features'])
            self.assertEqual(meta['features'], ['total_attempts', 'average_score', 'score_std'])


if __name__ == '__main__':
    unittest.main()
