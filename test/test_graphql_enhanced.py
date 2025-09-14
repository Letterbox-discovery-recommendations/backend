# tests/test_graphql_enhanced.py
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# Test: GraphQL sorting functionality
def test_query_peliculas_sort_by_title_asc():
    """Test sorting movies by title in ascending order"""
    query = '''
    query {
      peliculas(sort: "titulo") {
        id
        titulo
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    if len(movies) > 1:
        # Check if titles are in ascending order
        titles = [movie["titulo"] for movie in movies]
        assert titles == sorted(titles)


def test_query_peliculas_sort_by_title_desc():
    """Test sorting movies by title in descending order"""
    query = '''
    query {
      peliculas(sort: "titulo_desc") {
        id
        titulo
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    if len(movies) > 1:
        # Check if titles are in descending order
        titles = [movie["titulo"] for movie in movies]
        assert titles == sorted(titles, reverse=True)


def test_query_peliculas_sort_by_duration_asc():
    """Test sorting movies by duration in ascending order"""
    query = '''
    query {
      peliculas(sort: "duracionMinutos") {
        id
        titulo
        duracionMinutos
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    if len(movies) > 1:
        # Check if durations are in ascending order
        durations = [movie["duracionMinutos"] for movie in movies]
        assert durations == sorted(durations)


def test_query_peliculas_sort_by_duration_desc():
    """Test sorting movies by duration in descending order"""
    query = '''
    query {
      peliculas(sort: "duracionMinutos_desc") {
        id
        titulo
        duracionMinutos
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    if len(movies) > 1:
        # Check if durations are in descending order
        durations = [movie["duracionMinutos"] for movie in movies]
        assert durations == sorted(durations, reverse=True)


def test_query_peliculas_sort_by_release_date_asc():
    """Test sorting movies by release date in ascending order"""
    query = '''
    query {
      peliculas(sort: "fechaEstreno") {
        id
        titulo
        fechaEstreno
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    if len(movies) > 1:
        # Check if release dates are in ascending order (excluding null dates)
        dates = [movie["fechaEstreno"] for movie in movies if movie["fechaEstreno"]]
        if len(dates) > 1:
            assert dates == sorted(dates)


def test_query_peliculas_sort_by_release_date_desc():
    """Test sorting movies by release date in descending order"""
    query = '''
    query {
      peliculas(sort: "fechaEstreno_desc") {
        id
        titulo
        fechaEstreno
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    if len(movies) > 1:
        # Check if release dates are in descending order (excluding null dates)
        dates = [movie["fechaEstreno"] for movie in movies if movie["fechaEstreno"]]
        if len(dates) > 1:
            assert dates == sorted(dates, reverse=True)


def test_query_peliculas_with_rating():
    """Test querying movies with rating information"""
    query = '''
    query {
      peliculas {
        id
        titulo
        ratingPelicula
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    for movie in movies:
        assert "id" in movie
        assert "titulo" in movie
        assert "ratingPelicula" in movie
        # Rating should be None or a float between 0 and 5
        if movie["ratingPelicula"] is not None:
            assert isinstance(movie["ratingPelicula"], (int, float))
            assert 0 <= movie["ratingPelicula"] <= 5


def test_query_single_pelicula_by_id():
    """Test querying a single movie by ID"""
    # First get a movie ID
    query_all = '''
    query {
      peliculas {
        id
      }
    }
    '''
    response = client.post("/graphql", json={"query": query_all})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    
    if movies:
        movie_id = movies[0]["id"]
        
        # Now query that specific movie
        query_single = f'''
        query {{
          pelicula(id: {movie_id}) {{
            id
            titulo
            sinopsis
            duracionMinutos
            fechaEstreno
            posterUrl
            ratingPelicula
            director {{ id nombre }}
            generos {{ id nombre }}
            plataformas {{ id nombre }}
            elenco {{ personaje orden actor {{ id nombre }} }}
          }}
        }}
        '''
        response = client.post("/graphql", json={"query": query_single})
        result = response.json()
        assert "errors" not in result
        movie = result["data"]["pelicula"]
        assert movie is not None
        assert movie["id"] == movie_id
        assert "titulo" in movie
        assert "sinopsis" in movie
        assert "duracionMinutos" in movie


def test_query_pelicula_nonexistent_id():
    """Test querying a movie with non-existent ID"""
    query = '''
    query {
      pelicula(id: 99999) {
        id
        titulo
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert result["data"]["pelicula"] is None


def test_query_peliculas_combined_filters():
    """Test combining multiple filters"""
    query = '''
    query {
      peliculas(
        minDuration: 90,
        maxDuration: 180,
        minYear: 2000,
        maxYear: 2023,
        sort: "titulo"
      ) {
        id
        titulo
        duracionMinutos
        fechaEstreno
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    
    for movie in movies:
        # Check duration constraints
        assert 90 <= movie["duracionMinutos"] <= 180
        
        # Check year constraints if date exists
        if movie["fechaEstreno"]:
            year = int(movie["fechaEstreno"].split("-")[0])
            assert 2000 <= year <= 2023


def test_query_peliculas_filter_by_multiple_genres():
    """Test filtering by multiple genres"""
    query = '''
    query {
      peliculas(generos: ["Drama", "Action"]) {
        id
        titulo
        generos { nombre }
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    
    for movie in movies:
        genre_names = [genre["nombre"] for genre in movie["generos"]]
        # Should have at least one of the specified genres
        assert any(genre.lower() in ["drama", "action"] for genre in genre_names)


def test_query_peliculas_filter_by_multiple_platforms():
    """Test filtering by multiple platforms"""
    query = '''
    query {
      peliculas(plataformas: ["Netflix", "Amazon Prime"]) {
        id
        titulo
        plataformas { nombre }
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    movies = result["data"]["peliculas"]
    
    for movie in movies:
        platform_names = [platform["nombre"] for platform in movie["plataformas"]]
        # Should have at least one of the specified platforms
        assert any(platform.lower() in ["netflix", "amazon prime"] for platform in platform_names)


def test_query_personas_with_filter():
    """Test querying persons with name filter"""
    query = '''
    query {
      personas(nombre: "a") {
        id
        nombre
        genero
        imagenUrl
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    persons = result["data"]["personas"]
    
    for person in persons:
        assert "id" in person
        assert "nombre" in person
        assert "genero" in person
        assert "imagenUrl" in person
        # Name should contain the filter string
        assert "a" in person["nombre"].lower()


def test_query_plataformas():
    """Test querying all platforms"""
    query = '''
    query {
      plataformas {
        id
        nombre
        logoUrl
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    platforms = result["data"]["plataformas"]
    
    for platform in platforms:
        assert "id" in platform
        assert "nombre" in platform
        assert "logoUrl" in platform


def test_graphql_error_handling_invalid_query():
    """Test GraphQL error handling with invalid query"""
    query = '''
    query {
      invalidField {
        id
      }
    }
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" in result


def test_graphql_error_handling_malformed_query():
    """Test GraphQL error handling with malformed query"""
    query = '''
    query {
      peliculas {
        id
        titulo
        # Missing closing brace
    '''
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" in result
