import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.services.RecommendationsEngine import Recommendations
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.platform import Platform
from app.models.real_person import RealPerson
from app.models.ratings import Review
from datetime import datetime, timedelta
import numpy as np

@pytest.fixture
def db_session():
    # Crea una base SQLite en memoria y una sesión aislada por test
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def setup_movies_and_reviews(db_session):
    # Crear géneros y plataformas
    drama = Genre(nombre="Drama")
    comedy = Genre(nombre="Comedy")
    netflix = Platform(nombre="Netflix")
    hbo = Platform(nombre="HBO")
    db_session.add_all([drama, comedy, netflix, hbo])
    db_session.commit()
    # Crear películas
    m1 = Movie(titulo="Movie1", sinopsis="", duracionMinutos=100, generos=[drama], plataformas=[netflix])
    m2 = Movie(titulo="Movie2", sinopsis="", duracionMinutos=90, generos=[comedy], plataformas=[hbo])
    db_session.add_all([m1, m2])
    db_session.commit()
    # Crear usuario y reviews
    user = RealPerson(nombre="User1", genero="M")
    db_session.add(user)
    db_session.commit()
    r1 = Review(user_id=user.id, movie_id=m1.id, rating=5.0, created_at=datetime.utcnow())
    r2 = Review(user_id=user.id, movie_id=m2.id, rating=3.0, created_at=datetime.utcnow())
    db_session.add_all([r1, r2])
    db_session.commit()
    return m1, m2, user, drama, comedy, netflix, hbo

# Test: get_user_recommendations
def test_get_user_recommendations(db_session, setup_movies_and_reviews):
    m1, m2, user, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    liked = engine.get_user_recommendations(user.id)
    assert m1.id in liked
    assert m2.id not in liked

# Test: get_movie_vectors
def test_get_movie_vectors(db_session, setup_movies_and_reviews):
    m1, m2, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    vectors = engine.get_movie_vectors([m1, m2])
    assert isinstance(vectors[m1.id], np.ndarray)
    assert isinstance(vectors[m2.id], np.ndarray)
    assert np.sum(vectors[m1.id]) == 1  # Solo un género

# Test: get_recommendations (content-based)
def test_get_recommendations(db_session, setup_movies_and_reviews):
    m1, m2, user, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    recs = engine.get_recommendations(user_id=1)
    assert isinstance(recs, list)
    for movie, score in recs:
        assert isinstance(score, float)
        assert movie.id != m1.id  # No recomienda ya vistas

# Test: get_global_rankings
def test_get_global_rankings(db_session, setup_movies_and_reviews):
    engine = Recommendations(db_session)
    rankings = engine.get_global_rankings(limit=2)
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_viral_rankings
def test_get_viral_rankings(db_session, setup_movies_and_reviews):
    engine = Recommendations(db_session)
    rankings = engine.get_viral_rankings(limit=2)
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_rankings_by_platform
def test_get_rankings_by_platform(db_session, setup_movies_and_reviews):
    m1, m2, _, _, _, netflix, _ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    rankings = engine.get_rankings_by_platform(platform_id=netflix.id, limit=2)
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_rankings_by_genre
def test_get_rankings_by_genre(db_session, setup_movies_and_reviews):
    m1, m2, _, drama, _, _, _ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    rankings = engine.get_rankings_by_genre(genre_id=drama.id, limit=2)
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_collaborative_recommendations
def test_get_collaborative_recommendations(db_session, setup_movies_and_reviews):
    m1, m2, user, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    recs = engine.get_collaborative_recommendations(user_id=user.id, limit=2)
    assert isinstance(recs, list)
    for item in recs:
        assert "movie" in item and "score" in item

# Test: edge case - sin reviews
def test_recommendations_sin_reviews(db_session):
    engine = Recommendations(db_session)
    with pytest.raises(ValueError):
        engine.get_recommendations(user_id=1)

# Test: edge case - usuario sin ratings
def test_collaborative_sin_usuario(db_session, setup_movies_and_reviews):
    engine = Recommendations(db_session)
    recs = engine.get_collaborative_recommendations(user_id=9999, limit=2)
    assert recs == []
