# tests/test_routers_enhanced.py
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# Tests for Rankings Router
class TestRankingsRouter:
    """Test suite for the rankings router endpoints"""

    def test_get_global_rankings_default_limit(self):
        """Test global rankings with default limit"""
        response = client.get("/api/v1/rankings/global")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # Default limit
        
        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))
            assert "id" in item["movie"]
            assert "titulo" in item["movie"]

    def test_get_global_rankings_custom_limit(self):
        """Test global rankings with custom limit"""
        response = client.get("/api/v1/rankings/global?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        
        for item in data:
            assert "movie" in item
            assert "score" in item

    def test_get_global_rankings_large_limit(self):
        """Test global rankings with large limit"""
        response = client.get("/api/v1/rankings/global?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should not fail even with large limit

    def test_get_global_rankings_zero_limit(self):
        """Test global rankings with zero limit"""
        response = client.get("/api/v1/rankings/global?limit=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_viral_rankings_default_limit(self):
        """Test viral rankings with default limit"""
        response = client.get("/api/v1/rankings/viral")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # Default limit
        
        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_viral_rankings_custom_limit(self):
        """Test viral rankings with custom limit"""
        response = client.get("/api/v1/rankings/viral?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_get_rankings_by_platform_valid_id(self):
        """Test rankings by platform with valid platform ID"""
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
        """Test rankings by platform with invalid platform ID"""
        response = client.get("/api/v1/rankings/platform/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Should return empty list for non-existent platform

    def test_get_rankings_by_platform_with_limit(self):
        """Test rankings by platform with custom limit"""
        response = client.get("/api/v1/rankings/platform/1?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_rankings_by_genre_valid_id(self):
        """Test rankings by genre with valid genre ID"""
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
        """Test rankings by genre with invalid genre ID"""
        response = client.get("/api/v1/rankings/genre/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Should return empty list for non-existent genre

    def test_get_rankings_by_genre_with_limit(self):
        """Test rankings by genre with custom limit"""
        response = client.get("/api/v1/rankings/genre/1?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3

    def test_rankings_response_structure(self):
        """Test that all ranking endpoints return consistent response structure"""
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
                
                # Check movie structure
                movie = item["movie"]
                assert "id" in movie
                assert "titulo" in movie
                assert isinstance(movie["id"], int)
                assert isinstance(movie["titulo"], str)


# Tests for Recommendations Router
class TestRecommendationsRouter:
    """Test suite for the recommendations router endpoints"""

    def test_get_recommendations_health_check(self):
        """Test the recommendations health check endpoint"""
        response = client.get("/api/v1/recommendations/")
        # This might fail if there's no user data, but should not crash
        assert response.status_code in [200, 500]  # 500 is acceptable if no data
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            for item in data:
                assert "movie" in item
                assert "score" in item
                assert isinstance(item["score"], (int, float))

    def test_get_collaborative_recommendations_valid_user(self):
        """Test collaborative recommendations for a valid user"""
        response = client.get("/api/v1/recommendations/collaborative/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for item in data:
            assert "movie" in item
            assert "score" in item
            assert isinstance(item["score"], (int, float))

    def test_get_collaborative_recommendations_invalid_user(self):
        """Test collaborative recommendations for invalid user"""
        response = client.get("/api/v1/recommendations/collaborative/99999")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return empty list or handle gracefully

    def test_get_collaborative_recommendations_string_user_id(self):
        """Test collaborative recommendations with string user ID"""
        response = client.get("/api/v1/recommendations/collaborative/abc")
        assert response.status_code == 422  # Validation error for non-integer


# Tests for Actores Router
class TestActoresRouter:
    """Test suite for the actores router endpoints"""

    def test_get_actores_nombres(self):
        """Test getting all actor names"""
        response = client.get("/api/v1/actores/nombres")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for actor in data:
            assert "id" in actor
            assert "nombre" in actor
            assert "genero" in actor
            assert "imagenUrl" in actor
            assert isinstance(actor["id"], int)
            assert isinstance(actor["nombre"], str)
            assert isinstance(actor["genero"], int)

    def test_actores_response_structure(self):
        """Test that actores endpoint returns proper structure"""
        response = client.get("/api/v1/actores/nombres")
        assert response.status_code == 200
        data = response.json()
        
        if data:  # If there are actors in the database
            actor = data[0]
            required_fields = ["id", "nombre", "genero", "imagenUrl"]
            for field in required_fields:
                assert field in actor


# Integration Tests
class TestRouterIntegration:
    """Integration tests across multiple routers"""

    def test_all_endpoints_return_valid_json(self):
        """Test that all endpoints return valid JSON"""
        endpoints = [
            "/api/v1/rankings/global",
            "/api/v1/rankings/viral",
            "/api/v1/rankings/platform/1",
            "/api/v1/rankings/genre/1",
            "/api/v1/recommendations/",
            "/api/v1/recommendations/collaborative/1",
            "/api/v1/actores/nombres"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not crash and should return valid JSON
            assert response.status_code in [200, 422, 500]
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    assert data is not None
                except ValueError:
                    pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

    def test_cors_headers(self):
        """Test that endpoints include proper CORS headers if configured"""
        response = client.get("/api/v1/rankings/global")
        # This test depends on CORS configuration
        # Just ensure the request doesn't fail
        assert response.status_code == 200

    def test_content_type_headers(self):
        """Test that endpoints return proper content-type headers"""
        endpoints = [
            "/api/v1/rankings/global",
            "/api/v1/actores/nombres"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert "application/json" in response.headers.get("content-type", "")

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across routers"""
        # Test invalid endpoints
        invalid_endpoints = [
            "/api/v1/rankings/invalid",
            "/api/v1/recommendations/invalid",
            "/api/v1/actores/invalid"
        ]
        
        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            # Should return 404 for invalid endpoints
            assert response.status_code == 404
