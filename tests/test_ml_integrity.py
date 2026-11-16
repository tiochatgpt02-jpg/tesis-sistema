import csv
from io import BytesIO
from zipfile import ZipFile
import json
import numpy as np
import pytest
from sklearn.dummy import DummyClassifier
from ml.pipeline import trainer
from ml.pipeline.feature_builder import extract_features_from_records, determine_target_risk
from services.ml.feature_service import FeatureService
from ml.scripts.download_and_prepare_benchmark import prepare_benchmark_csv


def test_cutoff_excludes_unknown_dates_and_keeps_end_of_day_with_shared_engine():
    notes=[{'created_at':'2026-04-01T15:00:00-05:00','score':10,'activity_type':'actividades'},
           {'created_at':'2026-04-01T23:59:59','score':20,'activity_type':'evaluaciones'},
           {'created_at':'2026-04-02T00:00:00','score':0}, {'created_at':'invalid','score':0}, {'score':0}]
    result=extract_features_from_records(notes,cutoff_date='2026-04-01')
    assert result['total_attempts']==2 and result['average_score']==15
    assert result['last_score']==20 and result['average_evaluation_score']==20
    assert FeatureService.extract_features_from_records(notes,cutoff_date='2026-04-01')==result


@pytest.mark.parametrize('cutoff',['bad date','2026-02-30'])
def test_invalid_cutoff_never_disables_time_filter(cutoff):
    with pytest.raises(ValueError,match='corte'):
        extract_features_from_records([{'score':20}],cutoff_date=cutoff)


@pytest.mark.parametrize('score',[None,'',float('nan'),float('inf'),-1,21,'A'])
def test_invalid_note_is_never_silently_changed_to_zero(score):
    with pytest.raises(ValueError,match='notas'):
        extract_features_from_records([{'score':score,'activity_type':'evaluaciones'}])


@pytest.mark.parametrize('outcome',[{}, {'final_score':float('nan')}, {'is_at_risk':2}])
def test_unknown_outcome_never_becomes_passed_class(outcome):
    with pytest.raises(ValueError):determine_target_risk(outcome)


def test_single_grade_cannot_be_presented_as_student_prediction():
    from services.ml_service import build_prediction_payload
    result=build_prediction_payload('Demostracion',18)
    assert result['success'] is False and result['code']=='STUDENT_REQUIRED'
    assert result['risk_probability'] is None and result['predicted_class'] is None


def test_official_archive_adapter_uses_one_course_and_declares_artificial_dates(tmp_path):
    archive=tmp_path/'source.zip'
    with ZipFile(archive,'w') as zipped:
        zipped.writestr('student-por.csv','G1;G2;G3\n10;12;14\n5;6;7\n')
        zipped.writestr('student-mat.csv','G1;G2;G3\n1;1;1\n')
    output=tmp_path/'events.csv'
    assert prepare_benchmark_csv(output,archive)==4
    with output.open() as stream:rows=list(csv.DictReader(stream))
    assert {row['student_code'] for row in rows}=={'UCI-POR-0001','UCI-POR-0002'}
    assert [row['score'] for row in rows]==['10.0','12.0','5.0','6.0']
    assert rows[1]['final_score']=='14.0' and rows[3]['is_at_risk']=='1'
    meta=json.loads(output.with_name('dataset_metadata.json').read_text())
    assert meta['synthetic_event_dates'] is True and meta['chronological_cohorts'] is False


def test_model_selection_predictions_never_access_final_test(monkeypatch,tmp_path):
    X=np.arange(16,dtype=float).reshape(-1,1)
    y=np.array([0,1]*8)
    groups=np.array([f'fixture-{i}' for i in range(16)])
    metadata=[{'academic_period':'one'} for _ in y]
    monkeypatch.setattr(trainer,'load_training_matrix',lambda path:(X,y,groups,['marker'],metadata))
    monkeypatch.setattr(trainer,'partition_data',lambda *a,**k:(np.arange(12),np.arange(12,16),{'strategy':'group_split'}))
    monkeypatch.setattr(trainer,'build_candidate_classifiers',lambda:{'A':DummyClassifier(strategy='most_frequent'),'B':DummyClassifier(strategy='prior')})
    accesses=[]
    class RecordedPipeline:
        def __init__(self,model):self.model=model
        def fit(self,x,target):
            assert max(x[:,0])<12
            self.model.fit(x,target)
            return self
        def predict(self,x):
            accesses.append(tuple(x[:,0]))
            return self.model.predict(x)
        def predict_proba(self,x):return self.model.predict_proba(x)
    monkeypatch.setattr(trainer,'create_classification_pipeline',lambda model,**kwargs:RecordedPipeline(model))
    monkeypatch.setattr(trainer,'extract_feature_importances',lambda *a:{})
    monkeypatch.setattr(trainer.joblib,'dump',lambda *a:None)
    result=trainer.train_candidate_models(tmp_path/'fixture.csv',tmp_path/'models',split_strategy='group')
    test_access=[values for values in accesses if max(values)>=12]
    assert test_access==[(12.,13.,14.,15.)]
    assert max(accesses[-2])<12 and accesses[-1]==(12.,13.,14.,15.)
    assert result['validation_info']['test_used_for_selection'] is False
    assert result['validation_info']['selection_folds']==3
    assert result['metric_scope']=='independent_holdout_of_selected_model'


def test_temporal_request_cannot_fall_back_to_later_training_period():
    X=np.zeros((8,1));y=np.array([0,1]*4);groups=np.arange(8)
    meta=[{'academic_period':'2026-B1'}]*4+[{'academic_period':'2026-B2'}]*4
    with pytest.raises(ValueError,match='temporal'):
        trainer.partition_data(X,y,groups,meta,split_strategy='temporal',test_period='2026-B1')


def test_model_status_uses_final_metrics_and_never_fabricates_missing_values(monkeypatch):
    from types import SimpleNamespace
    from app import app
    from controllers import teacher_controller
    status={'name':'Fixture','test_metrics':{'accuracy':0.1234,'positive_class_recall':0.2345,
            'positive_class_f1':0.3456,'roc_auc':0.4567},'metric_scope':'independent_holdout_of_selected_model'}
    service=SimpleNamespace(get_status=lambda:status,is_available=lambda:True,
                            registry=SimpleNamespace(base_dir=__import__('pathlib').Path('nonexistent-fixture'),source='benchmark'))
    monkeypatch.setattr(teacher_controller,'get_risk_prediction_service',lambda:service)
    with app.test_client() as client:
        with client.session_transaction() as session:
            session.update(user='teacher',user_role='teacher',is_authenticated=True)
        page=client.get('/teacher/ml-status').get_data(as_text=True)
        assert '12.34%' in page and '23.45%' in page and '0.3456' in page
        assert '90.48%' not in page and 'Out-of-Time' not in page
        status['test_metrics']={}
        page=client.get('/teacher/ml-status').get_data(as_text=True)
        assert 'No disponible' in page and '91.15%' not in page and '90.48%' not in page
