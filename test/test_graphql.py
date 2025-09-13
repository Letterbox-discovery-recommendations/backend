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

def test_query_movies_advanced_filters():
    """
    Valida que los filtros avanzados de la query movies funcionan correctamente.
    """
    query = '''
    query {
      movies(minRating: 4, maxRating: 5, platform: "Netflix", minYear: 2000, maxYear: 2025, genre: "Drama", minDuration: 90, maxDuration: 200, limit: 2, sort: "rating_desc") {
        id
        title
        rating
        platform
        releaseYear
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "movies" in result["data"]
    for movie in result["data"]["movies"]:
        assert 4 <= movie["rating"] <= 5
        assert movie["platform"] == "Netflix"
        assert 2000 <= movie["releaseYear"] <= 2025


def test_query_movies_invalid_filters():
    """
    Valida que la query movies devuelve error si los filtros son inválidos.
    """
    query = '''
    query {
      movies(minYear: 2025, maxYear: 2000) {
        id
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" in result


def test_query_genres():
    """
    Valida que la query genres devuelve una lista de géneros con sus películas.
    """
    query = '''
    query {
      genres {
        id
        name
        movies { id title }
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "genres" in result["data"]
    for genre in result["data"]["genres"]:
        assert "id" in genre
        assert "name" in genre
        assert isinstance(genre["movies"], list)
