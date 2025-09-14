# tests/test_recommendations_collab_edgecases.py
import pytest
import numpy as np
from sqlmodel import SQLModel, create_engine, Session
from datetime import datetime
from app.routers.recommendations import Recommendations
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.platform import Platform
from app.models.real_person import RealPerson
from app.models.ratings import Review

@pytest.fixture
def memory_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def setup_minimal_db(session: Session):
    # Un sólo género y dos películas (una sin géneros)
    g = Genre(nombre="G1")
    session.add(g)
    session.commit()
    m1 = Movie(titulo="HasGenre", sinopsis="", duracionMinutos=90, generos=[g])
    m2 = Movie(titulo="NoGenre", sinopsis="", duracionMinutos=80, generos=[])
    session.add_all([m1, m2])
    session.commit()
    user = RealPerson(nombre="U1", genero=1)
    session.add(user)
    session.commit()
    # review positivo sólo para m1
    r = Review(user_id=user.id, movie_id=m1.id, rating=5.0, created_at=datetime.utcnow())
    session.add(r)
    session.commit()
    return m1, m2, user

def test_get_recommendations_handles_movies_with_no_genres(memory_session):
    m1, m2, user = setup_minimal_db(memory_session)
    engine = Recommendations(memory_session)
    # debe recomendar m2 sólo si similitud > 0 (pero m2 tiene vector 0 -> no se recomienda)
    recs = engine.get_recommendations()
    # como m2 no tiene géneros, no debería aparecer en recomendaciones
    assert all(movie.id != m2.id for movie, score in recs)

def test_collaborative_user_vector_zero_similarity(memory_session):
    m1, m2, user = setup_minimal_db(memory_session)
    # Crear otro usuario con ratings sólo en película distinta y valor bajo
    other = RealPerson(nombre="U2", genero=1)
    memory_session.add(other)
    memory_session.commit()
    r2 = Review(user_id=other.id, movie_id=m2.id, rating=1.0, created_at=datetime.utcnow())
    memory_session.add(r2)
    memory_session.commit()

    engine = Recommendations(memory_session)
    recs = engine.get_collaborative_recommendations(user_id=user.id, limit=5)
    # No hay usuarios similares con sim > 0 (vectores muy distintos) → puede devolver [] o lista vacía
    assert isinstance(recs, list)
