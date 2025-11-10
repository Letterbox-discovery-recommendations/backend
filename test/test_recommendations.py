import pytest
import asyncio
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
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
    # Use a normal (sync) SQLite engine/session and expose a tiny async
    # adapter that provides an `exec()` coroutine so the async
    # Recommendations methods can `await self.db_session.exec(...)`.
    from sqlmodel import create_engine, Session

    class SyncToAsyncSessionAdapter:
        def __init__(self, session: Session):
            self._session = session

        async def exec(self, stmt):
            # Run the synchronous DB call in a thread to avoid blocking.
            return await asyncio.to_thread(lambda: self._session.exec(stmt))

        # Provide attribute access to the underlying session for tests if needed
        def __getattr__(self, item):
            return getattr(self._session, item)

    # Crea una base SQLite en memoria y una sesión aislada por test.
    # Usamos StaticPool + check_same_thread=False para compartir la misma
    # conexión en memoria entre hilos (necesario cuando usamos
    # asyncio.to_thread en el adapter).
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    adapter = SyncToAsyncSessionAdapter(session)
    try:
        yield adapter
    finally:
        try:
            session.close()
        except Exception:
            pass
        try:
            engine.dispose()
        except Exception:
            pass

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
    liked = asyncio.run(engine.get_user_recommendations(user.id))
    assert m1.id in liked
    assert m2.id not in liked

# Test: get_movie_vectors
def test_get_movie_vectors(db_session, setup_movies_and_reviews):
    m1, m2, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    vectors = asyncio.run(engine.get_movie_vectors([m1, m2]))
    assert isinstance(vectors[m1.id], np.ndarray)
    assert isinstance(vectors[m2.id], np.ndarray)
    assert np.sum(vectors[m1.id]) == 1  # Solo un género

# Test: get_recommendations (content-based)
def test_get_recommendations(db_session, setup_movies_and_reviews):
    m1, m2, user, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    recs = asyncio.run(engine.get_recommendations(user_id=1))
    assert isinstance(recs, list)
    for movie, score in recs:
        assert isinstance(score, float)
        assert movie.id != m1.id  # No recomienda ya vistas

# Test: get_global_rankings
def test_get_global_rankings(db_session, setup_movies_and_reviews):
    engine = Recommendations(db_session)
    rankings = asyncio.run(engine.get_global_rankings(limit=2))
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_viral_rankings
def test_get_viral_rankings(db_session, setup_movies_and_reviews):
    engine = Recommendations(db_session)
    rankings = asyncio.run(engine.get_viral_rankings(limit=2))
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_rankings_by_platform
def test_get_rankings_by_platform(db_session, setup_movies_and_reviews):
    m1, m2, _, _, _, netflix, _ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    rankings = asyncio.run(engine.get_rankings_by_platform(platform_id=netflix.id, limit=2))
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_rankings_by_genre
def test_get_rankings_by_genre(db_session, setup_movies_and_reviews):
    m1, m2, _, drama, _, _, _ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    rankings = asyncio.run(engine.get_rankings_by_genre(genre_id=drama.id, limit=2))
    assert isinstance(rankings, list)
    for item in rankings:
        assert "movie" in item and "score" in item

# Test: get_collaborative_recommendations
def test_get_collaborative_recommendations(db_session, setup_movies_and_reviews):
    m1, m2, user, *_ = setup_movies_and_reviews
    engine = Recommendations(db_session)
    recs = asyncio.run(engine.get_collaborative_recommendations(user_id=user.id, limit=2))
    assert isinstance(recs, list)
    for item in recs:
        assert "movie" in item and "score" in item

# Test: edge case - sin reviews
def test_recommendations_sin_reviews(db_session):
    engine = Recommendations(db_session)
    with pytest.raises(ValueError):
        asyncio.run(engine.get_recommendations(user_id=1))


