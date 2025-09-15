from fastapi.testclient import TestClient
from app.main import app
import pytest
import app.routers.recommendations as recommendations_router
from unittest.mock import patch

client = TestClient(app)

# Test: GET /api/v1/recommendations/ (global recommendations)
def test_get_global_recommendations():
    user_id = 1
    response = client.get(f"/api/v1/recommendations/content/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "movie" in item and "score" in item

# Test: GET /api/v1/recommendations/collaborative/{user_id} (collaborative recommendations)
def test_get_collaborative_recommendations():
    user_id = 1  # Usa un ID válido en tu base de datos de test
    response = client.get(f"/api/v1/recommendations/collaborative/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "movie" in item and "score" in item

# Test: GET /api/v1/recommendations/collaborative/{user_id} (usuario no existe)
def test_get_collaborative_recommendations_usuario_no_existe():
    response = client.get("/api/v1/recommendations/collaborative/99999")
    assert response.status_code in (200, 404)  # Depende de tu implementación
    if response.status_code == 200:
        data = response.json()
        assert data == []

# Test: GET /api/v1/recommendations/ (sin recomendaciones)
def test_get_global_recommendations_sin_datos():
    with patch(
        "app.routers.recommendations.Recommendations.get_recommendations",
        return_value=[],
    ):
        user_id = 1
        response = client.get(f"/api/v1/recommendations/content/{user_id}")
        assert response.status_code == 200
        assert response.json() == []

# Test: Edge case - método no permitido
def test_post_not_allowed():
    user_id = 1

    response = client.post(f"/api/v1/recommendations/content/{user_id}")
    assert response.status_code == 405
