from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


def test_get_actor_names():
    """
    Valida que el endpoint /api/v1/actores/nombres responde correctamente y que los atributos existen.
    """
    response = client.get("/api/v1/actores/nombres")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for person in data:
        assert "id" in person
        assert "nombre" in person
        assert isinstance(person["id"], int)
        assert isinstance(person["nombre"], str)


def test_get_actor_names_not_found():
    """
    Simula que no hay actores usando la sobreescritura de dependencias de FastAPI.
    """
    import app.routers.actores as actores_router

    def fake_get_session():
        class DummySession:
            def exec(self, stmt):
                class DummyResult:
                    def all(self):
                        return []

                return DummyResult()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        yield DummySession()

    from app.main import app

    app.dependency_overrides[actores_router.get_session] = fake_get_session
    client = TestClient(app)
    response = client.get("/api/v1/actores/nombres")
    assert response.status_code == 200
    assert response.json() == []
    app.dependency_overrides = {}


def test_get_actor_names_invalid():
    """
    Valida que el endpoint responde con error si hay un fallo interno (simulado).
    """
    import app.routers.actores as actores_router

    def fake_get_session():
        raise Exception("DB error")

    from app.main import app

    app.dependency_overrides[actores_router.get_session] = fake_get_session
    client = TestClient(app)
    with pytest.raises(Exception) as excinfo:
        client.get("/api/v1/actores/nombres")
    assert "DB error" in str(excinfo.value)
    app.dependency_overrides = {}
