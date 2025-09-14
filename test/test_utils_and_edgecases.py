# tests/test_utils_and_edgecases.py
import numpy as np
import pytest

from app.services.RecommendationsEngine import (
    cosine_similarity_manual,
    vectorize_movie_genres,
)

class DummyMovie:
    def __init__(self, id, generos):
        self.id = id
        self.generos = generos

class DummyGenre:
    def __init__(self, nombre):
        self.nombre = nombre

def test_cosine_similarity_identical():
    a = np.array([1.0, 0.0, 1.0])
    b = np.array([1.0, 0.0, 1.0])
    assert pytest.approx(cosine_similarity_manual(a, b), rel=1e-6) == 1.0

def test_cosine_similarity_orthogonal():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert pytest.approx(cosine_similarity_manual(a, b), rel=1e-6) == 0.0

def test_cosine_similarity_zero_vector():
    a = np.array([0.0, 0.0])
    b = np.array([1.0, 2.0])
    assert cosine_similarity_manual(a, b) == 0.0

def test_vectorize_movie_genres_and_empty_genres():
    # definimos mapa de géneros
    genre_map = {"Horror": 0, "Drama": 1, "Comedy": 2}
    movie = DummyMovie(1, [DummyGenre("Drama"), DummyGenre("Horror")])
    vec = vectorize_movie_genres(movie, genre_map)
    assert isinstance(vec, np.ndarray)
    assert vec.shape[0] == len(genre_map)
    # indices 0(Horror) y 1(Drama) estén a 1
    assert vec[0] == 1 and vec[1] == 1 and vec[2] == 0

    # película sin géneros -> vector de ceros
    movie_empty = DummyMovie(2, [])
    vec_empty = vectorize_movie_genres(movie_empty, genre_map)
    assert np.all(vec_empty == 0)
