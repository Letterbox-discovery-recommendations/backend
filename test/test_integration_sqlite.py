from fastapi.testclient import TestClient
import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
import os

# Import app factory and DB utils
from app.main import app
import app.db.utils as db_utils
from app.models import Movie, Review, Genre, Platform


@pytest.fixture(scope="function")
def sqlite_engine():
    # Crear un engine SQLite en memoria compartido entre hilos
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Crear tablas
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def override_engine(sqlite_engine, monkeypatch):
    # Overwrite get_engine to return the in-memory sqlite engine
    monkeypatch.setattr(db_utils, "get_engine", lambda: sqlite_engine)
    # Also overwrite the module-level engine if present
    try:
        monkeypatch.setattr(db_utils, "engine", sqlite_engine)
    except Exception:
        pass
    yield


def seed_minimal_data(engine):
    with Session(engine) as session:
        m = Movie(id=1, titulo="Test Movie", sinopsis="s", duracionMinutos=90)
        session.add(m)
        # Add a positive review for another movie to allow recommendations/stats
        r = Review(movie_id=1, user_id=1, rating=5.0)
        session.add(r)
        session.commit()


def test_integration_sqlite(override_engine, sqlite_engine):
    # Seed data
    seed_minimal_data(sqlite_engine)

    client = TestClient(app)

    # Call rankings global
    r = client.get("/api/v1/rankings/global")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

    # Call recommendations (content) - requires auth dependency; patch it
    from app.security import get_current_user, TokenPayload
    app.dependency_overrides[get_current_user] = lambda: TokenPayload(
        sub="s", exp=9999999999, user_id=1, name="T", last_name="U", email="a@b", role="user", permissions=[], is_active=True, full_name="T U"
    )

    r2 = client.get("/api/v1/recommendations/content")
    assert r2.status_code == 200
    data2 = r2.json()
    assert isinstance(data2, list)

    # Clean up
    app.dependency_overrides.pop(get_current_user, None)
