import pytest
from sqlmodel import SQLModel
from app.models.actor import Actor
from app.models.movie import Movie
from app.models.genre import Genre


def test_actor_model():
    """
    Valida la creación de un Actor y todos sus atributos.
    """
    actor = Actor(id=1, name="John Doe", age=35, gender="M")
    assert actor.id == 1
    assert actor.name == "John Doe"
    assert actor.age == 35
    assert actor.gender == "M"


def test_actor_model_invalid():
    """
    Intenta crear y guardar un Actor sin nombre (debe fallar al hacer commit).
    """
    from sqlmodel import Session, create_engine, SQLModel
    from sqlalchemy.exc import IntegrityError

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        actor = Actor(age=40, gender="F")
        session.add(actor)
        with pytest.raises(IntegrityError):
            session.commit()


def test_movie_model():
    """
    Valida la creación de una Movie y todos sus atributos.
    """
    movie = Movie(
        id=1,
        title="Test Movie",
        description="A test movie",
        release_year=2020,
        director="Jane Doe",
        duration=120,
    )
    assert movie.id == 1
    assert movie.title == "Test Movie"
    assert movie.description == "A test movie"
    assert movie.release_year == 2020
    assert movie.director == "Jane Doe"
    assert movie.duration == 120


def test_movie_model_invalid():
    """
    Intenta crear y guardar una Movie sin título (debe fallar al hacer commit).
    """
    from sqlmodel import Session, create_engine, SQLModel
    from sqlalchemy.exc import IntegrityError

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        movie = Movie(
            description="No title", release_year=2021, director="X", duration=90
        )
        session.add(movie)
        with pytest.raises(IntegrityError):
            session.commit()


def test_genre_model():
    """
    Valida la creación de un Genre y todos sus atributos.
    """
    genre = Genre(id=1, name="Comedy", description="Funny movies")
    assert genre.id == 1
    assert genre.name == "Comedy"
    assert genre.description == "Funny movies"


def test_genre_model_optional_description():
    """
    Valida que la descripción de Genre puede ser None.
    """
    genre = Genre(id=2, name="Drama")
    assert genre.description is None
