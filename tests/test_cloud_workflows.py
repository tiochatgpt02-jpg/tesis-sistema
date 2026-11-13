import json
from datetime import datetime, timedelta, timezone
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

import pytest
from app import app
from config import Config
from services import learning_attempt_service as attempts
from services import llm_service
from services.grading_policy_service import academic_average
from services.teacher_note_service import build_gradebook_summary
from services.teacher_reports_service import build_academic_report


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(Config, 'USE_MOCK_DATA', True)
    monkeypatch.setattr(Config, 'AI_PROVIDER', 'groq')
    monkeypatch.setattr(Config, 'GROQ_API_KEY', 'test-secret-not-real')
    attempts._attempts.clear()
    attempts._permissions.clear()
    app.config.update(TESTING=True, SECRET_KEY='test-only')


def student(client, sid=1):
    with client.session_transaction() as s:
        s.update(user='demo', user_id=1, user_role='student', student_id=sid,
                 user_grade=5, user_section='A', is_authenticated=True)


def test_groq_request_and_bounded_timeout(monkeypatch):
    captured = {}
    def call(request, timeout):
        captured.update(url=request.full_url, payload=json.loads(request.data), timeout=timeout)
        return BytesIO(json.dumps({'choices':[{'message':{'content':'{"ok":true}'},'finish_reason':'stop'}]}).encode())
    monkeypatch.setattr(llm_service.urllib.request, 'urlopen', call)
    assert llm_service.generate_text('Devuelve JSON', timeout=180, json_mode=True) == '{"ok":true}'
    assert captured['url'] == 'https://api.groq.com/openai/v1/chat/completions'
    assert captured['timeout'] == Config.AI_TIMEOUT_SECONDS
    assert captured['payload']['response_format'] == {'type':'json_object'}


def test_nvidia_is_explicit_not_an_automatic_extra_wait(monkeypatch):
    monkeypatch.setattr(Config,'AI_PROVIDER','nvidia')
    monkeypatch.setattr(Config,'NVIDIA_API_KEY','test-nvidia')
    with patch.object(llm_service.urllib.request,'urlopen',return_value=BytesIO(b'{"choices":[{"message":{"content":"hola"}}]}')) as call:
        assert llm_service.generate_text('Hola') == 'hola'
    assert call.call_count == 1
    assert call.call_args.args[0].full_url == 'https://integrate.api.nvidia.com/v1/chat/completions'


def test_rate_limit_does_not_expose_provider_body_or_key():
    error = HTTPError('url',429,'secret detail',{},BytesIO(b'provider-secret'))
    with patch.object(llm_service.urllib.request,'urlopen',side_effect=error):
        with pytest.raises(llm_service.GenerationError,match='Cuota') as raised:
            llm_service.generate_text('private prompt')
    assert 'secret' not in str(raised.value)


def test_student_request_never_calls_external_model():
    with app.test_request_context('/student/api/test'):
        with patch.object(llm_service.urllib.request,'urlopen') as call:
            with pytest.raises(llm_service.GenerationError,match='contenido preparado'):
                llm_service.generate_text('test')
        call.assert_not_called()


def test_frozen_practice_exact_grading_idempotency_and_ownership():
    questions=[{'question':'Elige la herramienta','options':['Word','Excel'],'answer':'Word'}]
    record=attempts.start_attempt(1,4,'practice','material:1',questions)
    questions[0]['answer']='Excel'
    assert 'answer' not in attempts.public_attempt(record)['questions'][0]
    with pytest.raises(attempts.AttemptError):
        attempts.submit_attempt(record['id'],2,'practice','material:1',{'0':'Word'})
    with patch('services.db_service.record_student_result') as save:
        result=attempts.submit_attempt(record['id'],1,'practice','material:1',{'0':'W'})
        assert result['score']==0
        assert attempts.submit_attempt(record['id'],1,'practice','material:1',{'0':'Word'}) == result
    assert save.call_count == 1
    another=attempts.start_attempt(1,4,'practice','material:1',questions)
    assert another['id'] != record['id']


def test_exam_resume_single_attempt_and_teacher_reopening():
    questions=[{'question':'Pregunta','options':['A','B'],'answer':'A'}]
    record=attempts.start_attempt(1,4,'exam','3',questions,3)
    assert attempts.start_attempt(1,4,'exam','3',questions,3)['id']==record['id']
    with patch('services.db_service.record_student_result'),patch('services.db_service.record_student_assessment_attempt'):
        assert attempts.submit_attempt(record['id'],1,'exam','3',{'0':'A'})['score']==20
    with pytest.raises(attempts.AttemptError,match='Ya rendiste'):
        attempts.start_attempt(1,4,'exam','3',questions,3)
    attempts.reopen_exam(1,3,1)
    assert attempts.start_attempt(1,4,'exam','3',questions,3)['id']!=record['id']


def test_expired_exam_rejects_submission_and_reopening_closes_old_attempt():
    record=attempts.start_attempt(1,4,'exam','3',[{'question':'Q','answer':'A'}],3)
    attempts._attempts[record['id']]['started_at']=datetime.now(timezone.utc)-timedelta(minutes=31)
    with pytest.raises(attempts.AttemptError,match='tiempo'):
        attempts.submit_attempt(record['id'],1,'exam','3',{})
    attempts.reopen_exam(1,3,1)
    with pytest.raises(attempts.AttemptError,match='cerrado'):
        attempts.submit_attempt(record['id'],1,'exam','3',{})


def test_games_do_not_inflate_grade_and_overview_is_mean():
    notes=[{'student_id':1,'score':10,'activity_type':'evaluaciones'},
           {'student_id':2,'score':20,'activity_type':'evaluaciones'}]
    notes += [{'student_id':1,'score':20,'activity_type':'juegos'} for _ in range(9)]
    report=build_gradebook_summary(notes)
    assert report['overview']['average_score']==15
    assert next(s for s in report['students'] if s['student_id']==1)['average_score']==10


def test_report_excludes_other_bimesters():
    year=datetime.now().year
    report=build_academic_report([{'id':1,'grade':5}],
        [{'student_id':1,'score':10,'activity_type':'evaluaciones','created_at':f'{year}-03-10'},
         {'student_id':1,'score':20,'activity_type':'evaluaciones','created_at':f'{year}-08-10'}],period='1')
    assert report['rows'][0]['average']==10


def test_weights_use_latest_practice_and_missing_exam_remains_pending():
    notes=[{'student_id':1,'score':4,'activity_type':'actividades','item_type':'practice:material:1','id':1},
           {'student_id':1,'score':20,'activity_type':'actividades','item_type':'practice:material:1','id':2},
           {'student_id':1,'score':10,'activity_type':'evaluaciones','item_type':'exam:1'}]
    policy={'practice_weight':30,'exam_weight':70}
    assert academic_average(notes,policy)==13
    assert academic_average(notes[:2],policy) is None


@pytest.mark.parametrize('url',['/teacher/api/reports/gradebook','/teacher/api/reports/summary','/teacher/settings'])
def test_teacher_endpoints_reject_anonymous_and_students(url):
    with app.test_client() as client:
        assert client.get(url).status_code in (401,403,302)
        student(client)
        assert client.get(url).status_code in (401,403,302)


def test_published_exam_has_no_answer_keys_and_post_uses_server_attempt():
    exam={'id':9,'topic_id':4,'status':'PUBLISHED','questions':[{'id':2,'question':'Q','options':['Word','Excel'],'answer':'Word','approved':True}]}
    with app.test_client() as client:
        student(client)
        with patch('controllers.student_controller._published_topic_for_student',return_value={'id':4}), \
             patch('controllers.student_controller.fetch_assessments_for_topic',return_value=[exam]), \
             patch('controllers.student_controller.fetch_published_assessment_for_topic',return_value=exam):
            response=client.get('/student/api/topics/4/evaluation')
            assert response.status_code==200
            data=response.get_json()['evaluation']
            assert 'answer' not in data['questions'][0]
            with patch('services.db_service.record_student_result'),patch('services.db_service.record_student_assessment_attempt', return_value=17):
                result=client.post('/student/api/topics/4/evaluation',json={'attempt_id':data['attempt_id'],'answers':{'0':'Word'}})
            assert result.status_code==200
            assert result.get_json()['result']['score']==20


def test_material_practice_keeps_presentation_source_and_does_not_regenerate():
    material={'id':1,'topic_id':4,'title':'Word','status':'PUBLISHED'}
    pack={'questions':[{'question':'Q','options':['Word','Excel'],'answer':'Word'}],'source':'prepared'}
    with app.test_client() as client:
        student(client)
        with patch('controllers.student_controller.fetch_presentation_by_id',return_value=material), \
             patch('controllers.student_controller._published_topic_for_student',return_value={'id':4}), \
             patch('controllers.student_controller.MaterialExtractorService.extract_from_presentation_record',return_value={'raw_text':'Word'}), \
             patch('controllers.student_controller.get_practice',return_value=pack) as prepare, \
             patch('services.db_service.record_student_result'):
            data=client.get('/student/api/materials/1/practice?source=presentation').get_json()
            response=client.post('/student/api/materials/1/practice?source=presentation',json={'attempt_id':data['attempt_id'],'answers':{'0':'Word'}})
    assert response.status_code==200
    assert response.get_json()['score']==20
    assert prepare.call_count==1


def test_legacy_game_result_never_writes_an_academic_note():
    from services import db_service, mock_data
    before=list(mock_data.MOCK_STUDENT_NOTES)
    assert db_service.record_student_result(1,4,'juegos','game',20) is False
    assert mock_data.MOCK_STUDENT_NOTES == before


def test_six_simultaneous_submissions_record_one_grade():
    from concurrent.futures import ThreadPoolExecutor
    record=attempts.start_attempt(1,4,'practice','material:1',[{'question':'Q','answer':'A'}])
    with patch('services.db_service.record_student_result') as save:
        with ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _: attempts.submit_attempt(record['id'],1,'practice','material:1',{'0':'A'}),range(6)))
    assert save.call_count==1
    assert all(result['score']==20 for result in results)
