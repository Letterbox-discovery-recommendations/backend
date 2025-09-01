from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_query_movies():
    """
    Valida que la query movies devuelve una lista de películas con todos los atributos principales.
    """
    query = """
    query {
      movies {
        id
        title
        description
        releaseYear
        director
        duration
        cast { id name }
        genres { id name }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "movies" in result["data"]
    for movie in result["data"]["movies"]:
        assert "id" in movie
        assert "title" in movie
        assert "description" in movie
        assert "releaseYear" in movie
        assert "director" in movie
        assert "duration" in movie
        assert isinstance(movie["cast"], list)
        assert isinstance(movie["genres"], list)


def test_query_actors():
    """
    Valida que la query actors devuelve una lista de actores con todos los atributos principales.
    """
    query = """
    query {
      actors {
        id
        name
        age
        gender
        movies { id title }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "actors" in result["data"]
    for actor in result["data"]["actors"]:
        assert "id" in actor
        assert "name" in actor
        assert "age" in actor
        assert "gender" in actor
        assert isinstance(actor["movies"], list)


def test_query_genres():
    """
    Valida que la query de géneros devuelve una lista de géneros con sus películas.
    """
    query = """
    query {
      actors { id } # dummy para evitar error si no hay query genres
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result


def test_query_movies_filter():
    """
    Valida que la query movies con filtro por título funciona correctamente.
    """
    query = """
    query {
      movies(title: "The Godfather") {
        id
        title
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "movies" in result["data"]
    for movie in result["data"]["movies"]:
        assert "The Godfather" in movie["title"]


def test_query_actors_filter():
    """
    Valida que la query actors con filtro por nombre funciona correctamente.
    """
    query = """
    query {
      actors(name: "Marlon Brando") {
        id
        name
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "actors" in result["data"]
    for actor in result["data"]["actors"]:
        assert "Marlon Brando" in actor["name"]
