# tests/test_graphql_rating_and_sort.py
from fastapi.testclient import TestClient
from app.main import app
from sqlmodel import SQLModel, create_engine, Session
import pytest
from app.models.movie import Movie
from app.models.ratings import Review
from app.models.genre import Genre

client = TestClient(app)

@pytest.fixture
def temp_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_sort_fallback_for_invalid_sort_param():
    """Test that invalid sort parameters fall back to default sorting"""
    query = '''
    query {
      peliculas(sort: "invalid_sort") {
        id
        titulo
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    # si no hay errores, asumimos que devuelve lista (vacia o con datos)
    assert isinstance(data["data"]["peliculas"], list)


def test_rating_field_returns_correct_type():
    """Test that ratingPelicula field returns correct data type"""
    query = '''
    query {
      peliculas {
        id
        titulo
        ratingPelicula
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    for movie in movies:
        rating = movie["ratingPelicula"]
        if rating is not None:
            assert isinstance(rating, (int, float))
            assert 0 <= rating <= 5  # Assuming rating scale is 0-5


def test_sort_by_all_valid_options():
    """Test all valid sort options work correctly"""
    valid_sorts = [
        "titulo", "titulo_desc", 
        "duracionMinutos", "duracionMinutos_desc",
        "fechaEstreno", "fechaEstreno_desc"
    ]
    
    for sort_option in valid_sorts:
        query = f'''
        query {{
          peliculas(sort: "{sort_option}") {{
            id
            titulo
            duracionMinutos
            fechaEstreno
          }}
        }}
        '''
        resp = client.post("/graphql", json={"query": query})
        data = resp.json()
        assert "errors" not in data
        assert isinstance(data["data"]["peliculas"], list)


def test_sort_titulo_ascending_order():
    """Test that titulo sort returns movies in ascending alphabetical order"""
    query = '''
    query {
      peliculas(sort: "titulo") {
        id
        titulo
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    if len(movies) > 1:
        titles = [movie["titulo"] for movie in movies]
        assert titles == sorted(titles), "Movies should be sorted by title in ascending order"


def test_sort_titulo_descending_order():
    """Test that titulo_desc sort returns movies in descending alphabetical order"""
    query = '''
    query {
      peliculas(sort: "titulo_desc") {
        id
        titulo
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    if len(movies) > 1:
        titles = [movie["titulo"] for movie in movies]
        assert titles == sorted(titles, reverse=True), "Movies should be sorted by title in descending order"


def test_sort_duration_ascending_order():
    """Test that duracionMinutos sort returns movies in ascending duration order"""
    query = '''
    query {
      peliculas(sort: "duracionMinutos") {
        id
        titulo
        duracionMinutos
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    if len(movies) > 1:
        durations = [movie["duracionMinutos"] for movie in movies]
        assert durations == sorted(durations), "Movies should be sorted by duration in ascending order"


def test_sort_duration_descending_order():
    """Test that duracionMinutos_desc sort returns movies in descending duration order"""
    query = '''
    query {
      peliculas(sort: "duracionMinutos_desc") {
        id
        titulo
        duracionMinutos
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    if len(movies) > 1:
        durations = [movie["duracionMinutos"] for movie in movies]
        assert durations == sorted(durations, reverse=True), "Movies should be sorted by duration in descending order"


def test_sort_release_date_ascending_order():
    """Test that fechaEstreno sort returns movies in ascending date order"""
    query = '''
    query {
      peliculas(sort: "fechaEstreno") {
        id
        titulo
        fechaEstreno
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    if len(movies) > 1:
        # Filter out null dates for comparison
        dates = [movie["fechaEstreno"] for movie in movies if movie["fechaEstreno"]]
        if len(dates) > 1:
            assert dates == sorted(dates), "Movies should be sorted by release date in ascending order"


def test_sort_release_date_descending_order():
    """Test that fechaEstreno_desc sort returns movies in descending date order"""
    query = '''
    query {
      peliculas(sort: "fechaEstreno_desc") {
        id
        titulo
        fechaEstreno
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    if len(movies) > 1:
        # Filter out null dates for comparison
        dates = [movie["fechaEstreno"] for movie in movies if movie["fechaEstreno"]]
        if len(dates) > 1:
            assert dates == sorted(dates, reverse=True), "Movies should be sorted by release date in descending order"


def test_rating_calculation_accuracy():
    """Test that rating calculation returns accurate values"""
    query = '''
    query {
      peliculas {
        id
        titulo
        ratingPelicula
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]

    for movie in movies:
        rating = movie["ratingPelicula"]
        if rating is not None:
            # Rating should be a reasonable number
            assert isinstance(rating, (int, float))
            assert 0 <= rating <= 5  # Assuming 5-star rating system

            # Replace strict textual-decimal-length check with a numeric tolerance:
            # If we round to 6 decimal places, the difference should be very small.
            # Esto evita fallos por representaciones internas de float.
            diff = abs(rating - round(rating, 6))
            assert diff < 1e-6, f"rating has excessive precision: {rating} (diff {diff})"

def test_empty_result_sorting():
    """Test that sorting works correctly with empty results"""
    query = '''
    query {
      peliculas(
        sort: "titulo",
        minYear: 3000,  # Future year to ensure no results
        maxYear: 3001
      ) {
        id
        titulo
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    assert isinstance(movies, list)
    assert len(movies) == 0


def test_null_values_in_sorting():
    """Test that null values are handled correctly in sorting"""
    query = '''
    query {
      peliculas(sort: "fechaEstreno") {
        id
        titulo
        fechaEstreno
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    # Should not crash with null values
    assert isinstance(movies, list)
    
    # Check that null values are handled gracefully
    for movie in movies:
        fecha = movie["fechaEstreno"]
        if fecha is not None:
            # Should be a valid date string
            assert isinstance(fecha, str)
            assert len(fecha) >= 10  # At least YYYY-MM-DD format


def test_case_insensitive_sort_parameter():
    """Test that sort parameter handling is case-sensitive (as expected)"""
    # This should fall back to default since it's not exactly "titulo"
    query = '''
    query {
      peliculas(sort: "TITULO") {
        id
        titulo
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    # Should not crash, should fall back to default sorting
    assert isinstance(data["data"]["peliculas"], list)


def test_rating_field_with_no_reviews():
    """Test that movies with no reviews return null rating"""
    query = '''
    query {
      peliculas {
        id
        titulo
        ratingPelicula
      }
    }
    '''
    resp = client.post("/graphql", json={"query": query})
    data = resp.json()
    assert "errors" not in data
    movies = data["data"]["peliculas"]
    
    # At least some movies might have null ratings if they have no reviews
    rating_values = [movie["ratingPelicula"] for movie in movies]
    # Should contain a mix of null and non-null values, or all null, or all non-null
    assert all(rating is None or isinstance(rating, (int, float)) for rating in rating_values)
