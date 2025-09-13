from fastapi.testclient import TestClient
from app.main import app
import pytest 

client = TestClient(app)

# Test: Query all movies with all fields and relations
def test_query_peliculas():
    query = """
    query {
      peliculas {
        id
        titulo
        sinopsis
        duracionMinutos
        fechaEstreno
        posterUrl
        director { id nombre }
        elenco { personaje orden actor { id nombre } }
        generos { id nombre }
        plataformas { id nombre }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "id" in movie
        assert "titulo" in movie
        assert "sinopsis" in movie
        assert "duracionMinutos" in movie
        assert "elenco" in movie
        assert isinstance(movie["elenco"], list)
        assert "generos" in movie
        assert isinstance(movie["generos"], list)
        assert "plataformas" in movie
        assert isinstance(movie["plataformas"], list)

# Test: Filter movies by title
def test_query_peliculas_filter():
    query = """
    query {
      peliculas(titulo: "El Padrino") {
        id
        titulo
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "El Padrino" in movie["titulo"]

# Test: Query all persons (actors/directors)
def test_query_personas():
    query = """
    query {
      personas {
        id
        nombre
        genero
        imagenUrl
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "id" in person
        assert "nombre" in person
        assert "genero" in person
        assert "imagenUrl" in person

# Test: Filter persons by name
def test_query_personas_filter():
    query = """
    query {
      personas(nombre: "Marlon Brando") {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "Marlon Brando" in person["nombre"]

# Test: Query all genres
def test_query_generos():
    query = """
    query {
      generos {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "generos" in result["data"]
    for genero in result["data"]["generos"]:
        assert "id" in genero
        assert "nombre" in genero
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_peliculas():
    """
    Valida que la query peliculas devuelve una lista de películas con todos los atributos principales.
    """
    query = """
    query {
      peliculas {
        id
        titulo
        sinopsis
        duracionMinutos
        fechaEstreno
        posterUrl
        director { id nombre }
        elenco { personaje orden actor { id nombre } }
        generos { id nombre }
        plataformas { id nombre }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "id" in movie
        assert "titulo" in movie
        assert "sinopsis" in movie
        assert "duracionMinutos" in movie
        assert "elenco" in movie
        assert isinstance(movie["elenco"], list)
        assert "generos" in movie
        assert isinstance(movie["generos"], list)
        assert "plataformas" in movie
        assert isinstance(movie["plataformas"], list)

def test_query_peliculas_filter():
    """
    Valida que la query peliculas con filtro por título funciona correctamente.
    """
    query = """
    query {
      peliculas(titulo: "El Padrino") {
        id
        titulo
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "El Padrino" in movie["titulo"]

def test_query_personas():
    """
    Valida que la query personas devuelve una lista de personas reales con todos los atributos principales.
    """
    query = """
    query {
      personas {
        id
        nombre
        genero
        imagenUrl
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "id" in person
        assert "nombre" in person
        assert "genero" in person
        assert "imagenUrl" in person

def test_query_personas_filter():
    """
    Valida que la query personas con filtro por nombre funciona correctamente.
    """
    query = """
    query {
      personas(nombre: "Marlon Brando") {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "Marlon Brando" in person["nombre"]

def test_query_generos():
    """
    Valida que la query generos devuelve una lista de géneros.
    """
    query = """
    query {
      generos {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "generos" in result["data"]
    for genero in result["data"]["generos"]:
        assert "id" in genero
        assert "nombre" in genero
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_peliculas():
    """
    Valida que la query peliculas devuelve una lista de películas con todos los atributos principales.
    """
    query = """
    query {
      peliculas {
        id
        titulo
        sinopsis
        duracionMinutos
        fechaEstreno
        posterUrl
        director { id nombre }
        elenco { personaje orden actor { id nombre } }
        generos { id nombre }
        plataformas { id nombre }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "id" in movie
        assert "titulo" in movie
        assert "sinopsis" in movie
        assert "duracionMinutos" in movie
        assert "elenco" in movie
        assert isinstance(movie["elenco"], list)
        assert "generos" in movie
        assert isinstance(movie["generos"], list)
        assert "plataformas" in movie
        assert isinstance(movie["plataformas"], list)

def test_query_peliculas_filter():
    """
    Valida que la query peliculas con filtro por título funciona correctamente.
    """
    query = """
    query {
      peliculas(titulo: "El Padrino") {
        id
        titulo
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "El Padrino" in movie["titulo"]

def test_query_personas():
    """
    Valida que la query personas devuelve una lista de personas reales con todos los atributos principales.
    """
    query = """
    query {
      personas {
        id
        nombre
        genero
        imagenUrl
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "id" in person
        assert "nombre" in person
        assert "genero" in person
        assert "imagenUrl" in person

def test_query_personas_filter():
    """
    Valida que la query personas con filtro por nombre funciona correctamente.
    """
    query = """
    query {
      personas(nombre: "Marlon Brando") {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "Marlon Brando" in person["nombre"]

def test_query_generos():
    """
    Valida que la query generos devuelve una lista de géneros.
    """
    query = """
    query {
      generos {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "generos" in result["data"]
    for genero in result["data"]["generos"]:
        assert "id" in genero
        assert "nombre" in genero

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_peliculas():
    """
    Valida que la query peliculas devuelve una lista de películas con todos los atributos principales.
    """
    query = """
    query {
      peliculas {
        id
        titulo
        sinopsis
        duracionMinutos
        fechaEstreno
        posterUrl
        director { id nombre }
        elenco { personaje orden actor { id nombre } }
        generos { id nombre }
        plataformas { id nombre }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "id" in movie
        assert "titulo" in movie
        assert "sinopsis" in movie
        assert "duracionMinutos" in movie
        assert "elenco" in movie
        assert isinstance(movie["elenco"], list)
        assert "generos" in movie
        assert isinstance(movie["generos"], list)
        assert "plataformas" in movie
        assert isinstance(movie["plataformas"], list)

def test_query_peliculas_filter():
    """
    Valida que la query peliculas con filtro por título funciona correctamente.
    """
    query = """
    query {
      peliculas(titulo: "El Padrino") {
        id
        titulo
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "El Padrino" in movie["titulo"]

def test_query_personas():
    """
    Valida que la query personas devuelve una lista de personas reales con todos los atributos principales.
    """
    query = """
    query {
      personas {
        id
        nombre
        genero
        imagenUrl
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "id" in person
        assert "nombre" in person
        assert "genero" in person
        assert "imagenUrl" in person

def test_query_personas_filter():
    """
    Valida que la query personas con filtro por nombre funciona correctamente.
    """
    query = """
    query {
      personas(nombre: "Marlon Brando") {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "Marlon Brando" in person["nombre"]

def test_query_generos():
    """
    Valida que la query generos devuelve una lista de géneros.
    """
    query = """
    query {
      generos {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "generos" in result["data"]
    for genero in result["data"]["generos"]:
        assert "id" in genero
        assert "nombre" in genero
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_peliculas():
    """
    Valida que la query peliculas devuelve una lista de películas con todos los atributos principales.
    """
    query = """
    query {
      peliculas {
        id
        titulo
        sinopsis
        duracionMinutos
        fechaEstreno
        posterUrl
        director { id nombre }
        elenco { personaje orden actor { id nombre } }
        generos { id nombre }
        plataformas { id nombre }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "peliculas" in result["data"]
    for movie in result["data"]["peliculas"]:
        assert "id" in movie
        assert "titulo" in movie
        assert "sinopsis" in movie
        assert "duracionMinutos" in movie
        assert "elenco" in movie
        assert isinstance(movie["elenco"], list)
        assert "generos" in movie
        assert isinstance(movie["generos"], list)
        assert "plataformas" in movie
        assert isinstance(movie["plataformas"], list)

def test_query_personas():
    """
    Valida que la query personas devuelve una lista de personas reales con todos los atributos principales.
    """
    query = """
    query {
      personas {
        id
        nombre
        genero
        imagenUrl
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "id" in person
        assert "nombre" in person
        assert "genero" in person
        assert "imagenUrl" in person

def test_query_personas_filter():
    """
    Valida que la query personas con filtro por nombre funciona correctamente.
    """
    query = """
    query {
      personas(nombre: "Marlon Brando") {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "personas" in result["data"]
    for person in result["data"]["personas"]:
        assert "Marlon Brando" in person["nombre"]

def test_query_generos():
    """
    Valida que la query generos devuelve una lista de géneros.
    """
    query = """
    query {
      generos {
        id
        nombre
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    result = response.json()
    assert "errors" not in result
    assert "generos" in result["data"]
    for genero in result["data"]["generos"]:
        assert "id" in genero
        assert "nombre" in genero


