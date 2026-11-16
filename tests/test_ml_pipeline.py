"""Tests unitarios y de integración para el pipeline profesional de Machine Learning escolar."""

from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import app
from config import Config
from ml.pipeline.data_loader import MANDATORY_EVENT_COLUMNS, load_raw_csv, load_training_matrix
from ml.pipeline.feature_builder import CANONICAL_FEATURES, build_processed_matrix, extract_features_from_records
from ml.pipeline.predictor import AcademicRiskPredictor
from services.ml.model_registry import ModelRegistry, get_model_registry
from services.ml.prediction_service import RiskPredictionService


class TestDataLoaderAndValidation(unittest.TestCase):
    """1 y 2. Pruebas de validación de dataset inválido y columnas faltantes."""

    def test_missing_mandatory_columns_raises_informative_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            # Falta 'score' y 'final_status'
            f.write("student_code,academic_year,period,subject,event_date,activity_type\n")
            f.write("ALU-001,2024,B1,Matemática,2024-03-15,actividades\n")
            temp_path = Path(f.name)

        try:
            with self.assertRaises(ValueError) as ctx:
                load_raw_csv(temp_path)
            err_msg = str(ctx.exception).lower()
            self.assertIn("columnas obligatorias", err_msg)
            self.assertIn("score", err_msg)
            self.assertIn("final_status", err_msg)
        finally:
            if temp_path.is_file():
                temp_path.unlink()

    def test_invalid_dataset_empty_file_raises_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            temp_path = Path(f.name)

        try:
            with self.assertRaises(ValueError) as ctx:
                load_raw_csv(temp_path)
            self.assertIn("vacío", str(ctx.exception).lower())
        finally:
            if temp_path.is_file():
                temp_path.unlink()

    def test_invalid_vigesimal_scores_detected_and_handled(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("student_code,academic_year,period,subject,event_date,activity_type,score,final_status\n")
            # Nota fuera de rango vigesimal (> 20.0)
            f.write("ALU-001,2024,B1,Matemática,2024-03-15,actividades,25.0,aprobado\n")
            # Nota válida
            f.write("ALU-001,2024,B1,Matemática,2024-04-15,evaluaciones,16.0,aprobado\n")
            temp_path = Path(f.name)

        try:
            rows, quality = load_raw_csv(temp_path)
            self.assertEqual(quality['invalid_rows'], 1)
            self.assertEqual(quality['valid_events'], 1)
            self.assertEqual(rows[0]['score'], 16.0)
        finally:
            if temp_path.is_file():
                temp_path.unlink()


class TestTemporalLeakageAndFeatures(unittest.TestCase):
    """3 y 4. Pruebas de aislamiento temporal (anti-leakage) y consistencia de features.json."""

    def test_temporal_leakage_prevention_with_cutoff_date(self):
        notes = [
            {'event_date': '2024-03-01 10:00:00', 'score': 12.0, 'activity_type': 'actividades'},
            {'event_date': '2024-03-25 10:00:00', 'score': 14.0, 'activity_type': 'evaluaciones'},
            # Este evento es posterior a la fecha de corte y NO debe contaminar X
            {'event_date': '2024-05-10 10:00:00', 'score': 04.0, 'activity_type': 'evaluaciones'},
        ]

        feats_before_leak = extract_features_from_records(notes, cutoff_date='2024-04-01')
        self.assertEqual(feats_before_leak['total_attempts'], 2)
        self.assertEqual(feats_before_leak['average_score'], 13.0)
        self.assertEqual(feats_before_leak['last_score'], 14.0)

        # Si no hubiera cutoff, la nota baja de mayo bajaría el promedio a 10.0
        feats_all = extract_features_from_records(notes, cutoff_date=None)
        self.assertEqual(feats_all['total_attempts'], 3)
        self.assertEqual(feats_all['average_score'], 10.0)

    def test_feature_schema_consistency_with_features_json(self):
        benchmark_feat_json = Path("ml/datasets/benchmark/processed/features.json")
        if benchmark_feat_json.is_file():
            with benchmark_feat_json.open('r', encoding='utf-8') as f:
                data = json.load(f)
            saved_features = data.get('canonical_features', [])
            self.assertEqual(saved_features, CANONICAL_FEATURES)
            self.assertEqual(len(saved_features), 18)


class TestModelInferenceAndExplainability(unittest.TestCase):
    """5, 6 y 7. Modelo inexistente, alumno sin historial y explicaciones generadas."""

    def test_non_existent_model_returns_model_not_available_cleanly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            predictor = AcademicRiskPredictor(model_dir=Path(temp_dir))
            self.assertFalse(predictor.is_available())

            res = predictor.predict({'average_score': 14.0})
            self.assertFalse(res['success'])
            self.assertEqual(res['code'], 'MODEL_NOT_AVAILABLE')
            self.assertEqual(res['prediction']['risk_level'], 'UNKNOWN')

    def test_prediction_with_student_having_zero_history(self):
        predictor = AcademicRiskPredictor(model_dir=Path("ml/models/benchmark"))
        if predictor.is_available():
            empty_features = {'total_attempts': 0}
            res = predictor.predict(empty_features)
            self.assertTrue(res['success'])
            self.assertEqual(res['prediction']['risk_level'], 'UNKNOWN')
            self.assertEqual(res['risk_level'], 'Sin datos')
            self.assertIsNone(res['risk_probability'])
            self.assertIn("Sin historial previo", res['main_factors'][0])

    def test_explanations_generated_for_high_and_low_risk(self):
        predictor = AcademicRiskPredictor(model_dir=Path("ml/models/benchmark"))
        if predictor.is_available():
            # Caso en Riesgo Alto
            fail_features = {
                'total_attempts': 2,
                'evaluation_count': 1,
                'activities_count': 1,
                'average_score': 5.5,
                'average_evaluation_score': 5.0,
                'last_score': 5.0,
                'score_trend': -1.5,
            }
            res_fail = predictor.predict(fail_features)
            self.assertTrue(res_fail['success'])
            self.assertEqual(res_fail['prediction']['risk_level'], 'HIGH')
            self.assertGreaterEqual(res_fail['prediction']['probability'], 0.65)
            self.assertTrue(any("bajo" in f.lower() or "negativa" in f.lower() or "reprobatorio" in f.lower() for f in res_fail['main_factors']))
            self.assertTrue(len(res_fail['explanation']) > 0)

            # Caso en Riesgo Bajo
            pass_features = {
                'total_attempts': 4,
                'evaluation_count': 2,
                'activities_count': 2,
                'average_score': 17.0,
                'average_evaluation_score': 16.5,
                'last_score': 17.5,
                'score_trend': 1.0,
            }
            res_pass = predictor.predict(pass_features)
            self.assertTrue(res_pass['success'])
            self.assertEqual(res_pass['prediction']['risk_level'], 'LOW')
            self.assertLess(res_pass['prediction']['probability'], 0.35)
            self.assertTrue(any("destacado" in f.lower() or "mejora" in f.lower() or "constante" in f.lower() for f in res_pass['main_factors']))


class TestDatasetSourceSwitching(unittest.TestCase):
    """8. Cambio dinámico entre benchmark e institucional."""

    def test_source_switching_between_benchmark_and_institutional(self):
        # 1. Modo benchmark
        reg_bench = ModelRegistry(source='benchmark')
        self.assertEqual(reg_bench.source, 'benchmark')
        self.assertIn("benchmark", str(reg_bench.base_dir))
        self.assertTrue(reg_bench.is_available())

        # 2. Modo institucional (aún sin datos entrenados)
        reg_inst = ModelRegistry(source='institutional')
        self.assertEqual(reg_inst.source, 'institutional')
        self.assertIn("institutional", str(reg_inst.base_dir))
        self.assertFalse(reg_inst.is_available())

        meta_inst = reg_inst.get_metadata()
        self.assertEqual(meta_inst['status'], 'MODEL_NOT_AVAILABLE')
        self.assertIn("institucional", meta_inst['message'].lower())


class TestStudentRiskRestEndpoint(unittest.TestCase):
    """Endpoint GET /teacher/api/students/<id>/risk."""

    def test_get_student_risk_endpoint_with_auth(self):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'profesor1'
                sess['is_authenticated'] = True
                sess['user_role'] = 'teacher'

            res = client.get('/teacher/api/students/1/risk')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn('student_id', data)
            self.assertIn('prediction', data)
            self.assertIn('model', data)
            self.assertIn('explanation', data)
            self.assertIn('main_factors', data)


class TestRunPipelineSingleCommand(unittest.TestCase):
    """Prueba del orquestador único ml/run_pipeline.py."""

    def test_run_pipeline_benchmark_execution(self):
        from ml.run_pipeline import run_ml_pipeline

        with tempfile.TemporaryDirectory() as directory:
            summary = run_ml_pipeline(source='benchmark', split_strategy='temporal', cutoff_date='2024-04-30', output_root=Path(directory))
        self.assertEqual(summary['source'], 'benchmark')
        self.assertIn(summary['selected_algorithm'], {'RandomForest', 'GradientBoosting', 'LogisticRegression', 'DecisionTree'})
        self.assertGreater(summary['test_metrics']['accuracy'], 0.85)
        self.assertGreater(summary['test_metrics']['positive_class_recall'], 0.85)


if __name__ == '__main__':
    unittest.main()
