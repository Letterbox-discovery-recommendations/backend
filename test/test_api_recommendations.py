from fastapi.testclient import TestClient
from app.main import app
import pytest
from unittest.mock import patch

from app.security import get_current_user, TokenPayload

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_dependency(monkeypatch):
    """Sustituye la dependencia `get_current_user` por un usuario simulado para los tests.

    Esto evita llamadas al JWKS externo y permite controlar `user_id`.
    """
    fake_user = TokenPayload(
        sub="test-sub",
        exp=9999999999,
        user_id=1,
        name="Test",
        last_name="User",
        email="test@example.com",
        role="user",
        permissions=[],
        is_active=True,
        full_name="Test User",
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user

    # Parchear los métodos de Recommendations para no depender de la base de datos
    from app.models import Movie

    sample_movie = Movie(
        id=1,
        titulo="Pelicula Test",
        sinopsis="Sinopsis",
        duracionMinutos=100,
        fechaEstreno=None,
        posterUrl=None,
        activa=True,
        director_id=None,
    )

    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_recommendations",
        (lambda: None),
    )

    # The router awaits these service methods (they are async). Tests may
    # patch them, so provide async functions here so `await` works.
    async def _fake_get_recommendations(self, user_id):
        return [(sample_movie, 0.9)]

    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_recommendations",
        _fake_get_recommendations,
    )

    async def _fake_get_collaborative(self, user_id):
        # note: some implementations accept (self, user_id) or (user_id,) when
        # patched at the class level; this definition will receive 'self' when
        # bound as a function on the class by monkeypatch.setattr.
        return [{"movie": sample_movie, "score": 0.8}]

    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_collaborative_recommendations",
        _fake_get_collaborative,
    )

    yield

    app.dependency_overrides.pop(get_current_user, None)


# Test: GET /api/v1/recommendations/content (global recommendations)
def test_get_global_recommendations():
    response = client.get("/api/v1/recommendations/content")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "movie" in item and "score" in item


# Test: GET /api/v1/recommendations/collaborative (collaborative recommendations)
def test_get_collaborative_recommendations():
    response = client.get("/api/v1/recommendations/collaborative")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "movie" in item and "score" in item


# Test: GET /api/v1/recommendations/collaborative (usuario no existe)
def test_get_collaborative_recommendations_usuario_no_existe(monkeypatch):
    # Override auth to simulate a non-existent user id
    fake_user = TokenPayload(
        sub="test-sub",
        exp=9999999999,
        user_id=99999,
        name="No",
        last_name="User",
        email="no@example.com",
        role="user",
        permissions=[],
        is_active=True,
        full_name="No User",
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user

    # Para este caso específico, parcheamos el método para devolver []
    async def _fake_collab_empty(self, user_id):
        return []

    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_collaborative_recommendations",
        _fake_collab_empty,
    )

    response = client.get("/api/v1/recommendations/collaborative")
    # Según la implementación, cuando no hay ratings la función devuelve []
    assert response.status_code == 200
    assert response.json() == []


# Test: GET /api/v1/recommendations/content (sin recomendaciones)
def test_get_global_recommendations_sin_datos():
    async def _fake_empty_get_recommendations(self, user_id):
        return []

    with patch(
        "app.routers.recommendations.Recommendations.get_recommendations",
        new=_fake_empty_get_recommendations,
    ):
        response = client.get("/api/v1/recommendations/content")
        assert response.status_code == 200
        assert response.json() == []


# Test: Edge case - método no permitido
def test_post_not_allowed():
    response = client.post("/api/v1/recommendations/content")
    assert response.status_code == 405
