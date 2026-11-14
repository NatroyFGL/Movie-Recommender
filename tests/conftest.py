import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from api.database import get_session
from api.main import app
from scripts.seed_db import seed

FAKE_POSTER = 'https://example.com/poster.jpg'


@pytest.fixture(scope='module')
def test_engine(tmp_path_factory):
    db_file = tmp_path_factory.mktemp('db') / 'test.db'
    engine = create_engine(f'sqlite:///{db_file}', connect_args={'check_same_thread': False})
    seed(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope='module')
def client(test_engine):
    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def fake_posters(monkeypatch):
    monkeypatch.setattr('api.main.get_poster', lambda movie_id: FAKE_POSTER)
