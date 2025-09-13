import pytest
from sqlmodel import SQLModel
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.platform import Platform
from app.models.real_person import RealPerson
from app.models.links import CastLink
from sqlmodel import Session, create_engine
from sqlalchemy.exc import IntegrityError

def test_real_person_model():
    """
    Valida la creación de un RealPerson y todos sus atributos.
    """
    person = RealPerson(id=1, nombre="John Doe", genero=1, imagenUrl="url")
    assert person.id == 1
    assert person.nombre == "John Doe"
    assert person.genero == 1
    assert person.imagenUrl == "url"


def test_real_person_model_invalid():
    """
    Intenta crear y guardar un RealPerson sin nombre (debe fallar al hacer commit).
    """
    from sqlmodel import Session, create_engine, SQLModel
    from sqlalchemy.exc import IntegrityError

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        person = RealPerson(genero=1)
        session.add(person)
        with pytest.raises(IntegrityError):
            session.commit()


def test_movie_model():
    """
    Valida la creación de una Movie y todos sus atributos.
    """
    from datetime import date

    movie = Movie(
        id=1,
        titulo="Test Movie",
        sinopsis="A test movie",
        duracionMinutos=120,
        fechaEstreno=date(2020, 1, 1),
        posterUrl="url",
        director_id=1,
    )
    assert movie.id == 1
    assert movie.titulo == "Test Movie"
    assert movie.sinopsis == "A test movie"
    assert movie.duracionMinutos == 120
    assert movie.fechaEstreno == date(2020, 1, 1)
    assert movie.posterUrl == "url"
    assert movie.director_id == 1


def test_movie_model_invalid():
    """
    Intenta crear y guardar una Movie sin título (debe fallar al hacer commit).
    """

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        movie = Movie(sinopsis="No title", duracionMinutos=90)
        session.add(movie)
        with pytest.raises(IntegrityError):
            session.commit()


def test_genre_model():
    """
    Valida la creación de un Genre y todos sus atributos.
    """
    genre = Genre(id=1, nombre="Comedy")
    assert genre.id == 1
    assert genre.nombre == "Comedy"


def test_platform_model():
    """
    Valida la creación de una Platform y todos sus atributos.
    """
    platform = Platform(id=1, nombre="Netflix", logoUrl="logo.png")
    assert platform.id == 1
    assert platform.nombre == "Netflix"
    assert platform.logoUrl == "logo.png"


def test_castlink_model():
    """
    Valida la creación de un CastLink y todos sus atributos.
    """
    link = CastLink(movie_id=1, person_id=2, personaje="Protagonista", orden=1)
    assert link.movie_id == 1
    assert link.person_id == 2
    assert link.personaje == "Protagonista"
    assert link.orden == 1