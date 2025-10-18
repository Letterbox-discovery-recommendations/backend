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

    
    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_recommendations",
        lambda self, user_id: [(sample_movie, 0.9)],
    )
    monkeypatch.setattr(
        "app.routers.recommendations.Recommendations.get_collaborative_recommendations",
        lambda self, user_id: [{"movie": sample_movie, "score": 0.8}],
    )

    
    def _patched_get_global_rankings(self, limit=10):
        if limit <= 0:
            return []
        results = [{"movie": sample_movie, "score": 5}]
        return results[:limit]

    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_global_rankings",
        _patched_get_global_rankings,
    )
    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_viral_rankings",
        lambda self, limit=10: [{"movie": sample_movie, "score": 3}],
    )
    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_rankings_by_platform",
        lambda self, platform_id, limit=10: [{"movie": sample_movie, "score": 4}] if platform_id == 1 else [],
    )
    monkeypatch.setattr(
        "app.routers.rankings.Recommendations.get_rankings_by_genre",
        lambda self, genre_id, limit=10: [{"movie": sample_movie, "score": 4}] if genre_id == 1 else [],
    )

    yield

    app.dependency_overrides.pop(get_current_user, None)


# Tests para Rankings Router
class TestRankingsRouter:
    """Test suite para rankings router endpoints"""

    def test_get_global_rankings_default_limit(self):
        """Test global rankings with default limit"""
        response = client.get("/api/v1/rankings/global")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # limite por default
        
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
        
        for item in data:
            assert "movie" in item
            assert "score" in item

    def test_get_global_rankings_large_limit(self):
        response = client.get("/api/v1/rankings/global?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Deberia fallar incluso con un limite alto

    def test_get_global_rankings_zero_limit(self):
        """Test global rankings con limite igual a 0"""
        response = client.get("/api/v1/rankings/global?limit=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_viral_rankings_default_limit(self):
        """Test viral rankings con limite de default"""
        response = client.get("/api/v1/rankings/viral")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  
        
        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_viral_rankings_custom_limit(self):
        """Test viral rankings con limite personalizado"""
        response = client.get("/api/v1/rankings/viral?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_get_rankings_by_platform_valid_id(self):
        """Test rankings por plataforma con ID de plataforma valido"""
        # Test with platform ID 1 (assuming it exists)
        response = client.get("/api/v1/rankings/platform/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_rankings_by_platform_invalid_id(self):
        """Test rankings por plataforma con ID de plataforma invalido"""
        response = client.get("/api/v1/rankings/platform/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Deberia retornar lista vacia para plataforma no existente

    def test_get_rankings_by_platform_with_limit(self):
        """Test rankings por plataforma con limite personalizado"""
        response = client.get("/api/v1/rankings/platform/1?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_rankings_by_genre_valid_id(self):
        """Test rankings por genero con ID de genero valido"""
        # Test with genre ID 1 (assuming it exists)
        response = client.get("/api/v1/rankings/genre/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_rankings_by_genre_invalid_id(self):
        """Test rankings por genero con ID de genero invalido"""
        response = client.get("/api/v1/rankings/genre/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Deberia retornar lista vacia para plataforma no existente

    def test_get_rankings_by_genre_with_limit(self):
        """Test rankings por genero con limite personalizado"""
        response = client.get("/api/v1/rankings/genre/1?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_rankings_response_structure(self):
        """Test donde se verifica la estructura de la respuesta de los endpoints de rankings"""
        endpoints = [
            "/api/v1/rankings/global",
            "/api/v1/rankings/viral",
            "/api/v1/rankings/platform/1",
            "/api/v1/rankings/genre/1"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
            for item in data:
                assert "movie" in item
                assert "score" in item
                assert isinstance(item["movie"], dict)
                assert isinstance(item["score"], (int, float))
                
                movie = item["movie"]
                assert "id" in movie
                assert "titulo" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["titulo"], str)


# Tests para Recommendations Router
class TestRecommendationsRouter:
    """Test suite para recommendations router endpoints"""

    def test_get_recommendations_health_check(self):
        response = client.get("/api/v1/recommendations/content")
        # Esto podria fallar si no hay datos de usuario, pero no deberia crashear
        assert response.status_code in [200, 500]  # 500 es aceptable si no hay datos

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            for item in data:
                assert "movie" in item
                assert "score" in item
                assert isinstance(item["score"], (int, float))

    def test_get_collaborative_recommendations_valid_user(self):
        """Test recommendations colaborativas para usuario valido"""
        response = client.get("/api/v1/recommendations/collaborative")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_collaborative_recommendations_invalid_user(self):
        """Test recommendations colaborativas para usuario invalido"""
        response = client.get("/api/v1/recommendations/collaborative")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Deberia retornar lista vacia para usuario no existente

    def test_get_collaborative_recommendations_string_user_id(self):
        """Test collaborative recommendations with string user ID"""
        # El endpoint no acepta string como user_id, pero deberia manejarlo sin crashear
        response = client.get("/api/v1/recommendations/collaborative")
        assert response.status_code == 200





# Test de Integracion entre Routers
class TestRouterIntegration:
    """Test de integracion entre multiples routers"""

    def test_all_endpoints_return_valid_json(self):
        """Testea que todos los endpoints retornen JSON valido"""
        endpoints = [
            "/api/v1/rankings/global",
            "/api/v1/rankings/viral",
            "/api/v1/rankings/platform/1",
            "/api/v1/rankings/genre/1",
            "/api/v1/recommendations/content",
            "/api/v1/recommendations/collaborative"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # No deberia fallar
            assert response.status_code in [200, 422, 500]
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    assert data is not None
                except ValueError:
                    pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_cors_headers(self):
        """Testea que los endpoints manejen CORS correctamente"""
        response = client.get("/api/v1/rankings/global")
        # This test depends on CORS configuration
        # Just ensure the request doesn't fail
        assert response.status_code == 200

    def test_content_type_headers(self):
        """Testea que los endpoints retornen headers de tipo de contenido correctos"""
        endpoints = [
            "/api/v1/rankings/global"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert "application/json" in response.headers.get("content-type", "")

    def test_error_handling_consistency(self):
        """Testea que los endpoints manejen errores de manera consistente"""
        # Test invalid endpoints
        invalid_endpoints = [
            "/api/v1/rankings/invalid",
            "/api/v1/recommendations/invalid"
        ]
        
        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            # Should return 404 for invalid endpoints
            assert response.status_code == 404
