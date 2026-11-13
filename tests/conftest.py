"""Each test starts with isolated, fictitious data and no production credentials."""
from copy import deepcopy
import pytest
from config import Config
from services import db_service, mock_data
from services import learning_attempt_service, grading_policy_service, practice_service

_baseline = {name: deepcopy(value) for name,value in vars(mock_data).items() if name.startswith('MOCK_')}


@pytest.fixture(autouse=True)
def isolated_academic_data(monkeypatch):
    monkeypatch.setattr(Config,'USE_MOCK_DATA',True)
    monkeypatch.setattr(Config,'DATABASE_URL','')
    monkeypatch.setattr(Config,'GROQ_API_KEY','')
    monkeypatch.setattr(Config,'NVIDIA_API_KEY','')
    monkeypatch.setattr(db_service,'_use_mock',lambda: Config.USE_MOCK_DATA)
    for name,value in _baseline.items():
        monkeypatch.setattr(mock_data,name,deepcopy(value))
    learning_attempt_service._attempts.clear()
    learning_attempt_service._permissions.clear()
    practice_service._prepared.clear()
    monkeypatch.setattr(grading_policy_service,'_policy',None)
