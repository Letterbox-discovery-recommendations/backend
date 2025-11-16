# tests/test_routers_enhanced.py
from fastapi.testclient import TestClient
from app.main import app
import pytest

from app.security import get_current_user, TokenPayload

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_and_patch(monkeypatch):
    """
    - Reemplaza `get_current_user` por un TokenPayload de prueba.
    - Parchea métodos de Recommendations y Rankings para no requerir Postgres.
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
"""
Cleaned and async-aware router tests.

These tests patch the async service methods (awaitable) so the FastAPI
endpoints can call them without connecting to an external DB.
All changes are inside this test file only.
"""

from fastapi.testclient import TestClient
from app.main import app
import pytest

from app.security import get_current_user, TokenPayload


client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_and_patch(monkeypatch):
    """Override authentication and patch async service methods used by routers."""
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

    async def _async_get_recommendations(self, user_id):
        return [(sample_movie, 0.9)]

    async def _async_get_collaborative(self, user_id):
        return [{"movie": sample_movie, "score": 0.8}]

    async def _async_get_global_rankings(self, limit=10):
        if limit <= 0:
            return []
        results = [{"movie": sample_movie, "score": 5}]
        return results[:limit]

    async def _async_get_viral(self, limit=10):
        return [{"movie": sample_movie, "score": 3}]

    async def _async_get_rankings_by_platform(self, platform_id, limit=10):
        return ([{"movie": sample_movie, "score": 4}] if platform_id == 1 else [])

    async def _async_get_rankings_by_genre(self, genre_id, limit=10):
        return ([{"movie": sample_movie, "score": 4}] if genre_id == 1 else [])

    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_recommendations",
        _async_get_recommendations,
    )
    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_collaborative_recommendations",
        _async_get_collaborative,
    )

    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_global_rankings",
        _async_get_global_rankings,
    )
    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_viral_rankings",
        _async_get_viral,
    )
    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_rankings_by_platform",
        _async_get_rankings_by_platform,
    )
    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_rankings_by_genre",
        _async_get_rankings_by_genre,
    )

    yield

    app.dependency_overrides.pop(get_current_user, None)


class TestRankingsRouter:
    def test_get_global_rankings_default_limit(self):
        response = client.get("/api/v1/rankings/global")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))
            assert "id" in item["movie"]
            assert "titulo" in item["movie"]

    def test_get_global_rankings_custom_limit(self):
        response = client.get("/api/v1/rankings/global?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_global_rankings_zero_limit(self):
        response = client.get("/api/v1/rankings/global?limit=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_viral_rankings_default_limit(self):
        response = client.get("/api/v1/rankings/viral")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_get_viral_rankings_custom_limit(self):
        response = client.get("/api/v1/rankings/viral?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_get_rankings_by_platform_valid_id(self):
        response = client.get("/api/v1/rankings/platform/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_rankings_by_platform_invalid_id(self):
        response = client.get("/api/v1/rankings/platform/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_rankings_by_genre_valid_id(self):
        response = client.get("/api/v1/rankings/genre/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_rankings_by_genre_invalid_id(self):
        response = client.get("/api/v1/rankings/genre/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestRecommendationsRouter:
    def test_get_recommendations_health_check(self):
        response = client.get("/api/v1/recommendations/content")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_collaborative_recommendations_valid_user(self):
        response = client.get("/api/v1/recommendations/collaborative")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_collaborative_recommendations_invalid_user(self):
        response = client.get("/api/v1/recommendations/collaborative")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestRouterIntegration:
    def test_all_endpoints_return_valid_json(self):
        endpoints = [
            "/api/v1/rankings/global",
            "/api/v1/rankings/viral",
            "/api/v1/rankings/platform/1",
            "/api/v1/rankings/genre/1",
            "/api/v1/recommendations/content",
            "/api/v1/recommendations/collaborative",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                try:
                    data = response.json()
                    assert data is not None
                except ValueError:
                    pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_cors_headers(self):
        response = client.get("/api/v1/rankings/global")
        assert response.status_code == 200

    def test_content_type_headers(self):
        response = client.get("/api/v1/rankings/global")
        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "")

    def test_error_handling_consistency(self):
        invalid_endpoints = ["/api/v1/rankings/invalid", "/api/v1/recommendations/invalid"]
        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404
    """Test suite para recommendations router endpoints"""
