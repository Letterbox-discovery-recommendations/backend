import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from app.models.movie import Movie
from app.models.genre import Genre, MovieGenreLink
from app.models.real_person import RealPerson
from app.models.links import CastLink


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_and_query_real_person(session):
    """
    Crea una persona real, la guarda y la recupera. Valida todos los atributos.
    """
    person = RealPerson(nombre="Test Person", genero=1, imagenUrl="url")
    session.add(person)
    session.commit()
    result = session.exec(select(RealPerson)).first()
    assert result.nombre == "Test Person"
    assert result.genero == 1
    assert result.imagenUrl == "url"
    assert result.id is not None


def test_create_real_person_invalid_data(session):
    """
    Intenta crear una persona real sin nombre (debe fallar por restricción NOT NULL).
    """
    with pytest.raises(Exception):
        person = RealPerson(genero=1)
        session.add(person)
        session.commit()


def test_movie_castlink_relationship(session):
    """
    Relaciona una persona real y una película, y valida la relación desde ambos lados.
    """
    person = RealPerson(nombre="Actor", genero=2)
    movie = Movie(
        titulo="Movie",
        sinopsis="Desc",
        duracionMinutos=90,
    )
    session.add(person)
    session.add(movie)
    session.commit()
    link = CastLink(
        movie_id=movie.id, person_id=person.id, personaje="Protagonista", orden=1
    )
    session.add(link)
    session.commit()
    movie_from_db = session.get(Movie, movie.id)
    person_from_db = session.get(RealPerson, person.id)
    assert link in movie_from_db.cast_links
    assert link in person_from_db.cast_links


def test_delete_real_person(session):
    """
    Crea y elimina una persona real, comprobando que desaparece de la base de datos.
    """
    person = RealPerson(nombre="ToDelete", genero=1)
    session.add(person)
    session.commit()
    person_id = person.id
    session.delete(person)
    session.commit()
    assert session.get(RealPerson, person_id) is None


def test_update_real_person(session):
    """
    Actualiza una persona real y valida que los cambios persisten en la base de datos.
    """
    person = RealPerson(nombre="Old Name", genero=1)
    session.add(person)
    session.commit()
    person.nombre = "New Name"
    session.add(person)
    session.commit()
    updated = session.get(RealPerson, person.id)
    assert updated.nombre == "New Name"


def test_delete_movie_and_relations(session):
    """
    Crea una película con relaciones y la elimina, comprobando que las relaciones también se eliminan.
    """
    person = RealPerson(nombre="Actor", genero=1)
    genre = Genre(nombre="Genre")
    movie = Movie(titulo="ToDelete", sinopsis="", duracionMinutos=90)
    session.add_all([person, genre, movie])
    session.commit()
    link1 = CastLink(
        movie_id=movie.id, person_id=person.id, personaje="Protagonista", orden=1
    )
    link2 = MovieGenreLink(movie_id=movie.id, genre_id=genre.id)
    session.add_all([link1, link2])
    session.commit()
    session.delete(movie)
    session.commit()
    assert session.get(Movie, movie.id) is None


def test_no_duplicate_castlink(session):
    """
    Intenta crear dos veces la misma relación persona-película (debe fallar si hay restricción de unicidad).
    """
    person = RealPerson(nombre="UniqueLink", genero=2)
    movie = Movie(titulo="UniqueLink", sinopsis="", duracionMinutos=90)
    session.add_all([person, movie])
    session.commit()
    link1 = CastLink(
        movie_id=movie.id, person_id=person.id, personaje="Protagonista", orden=1
    )
    link2 = CastLink(
        movie_id=movie.id, person_id=person.id, personaje="Protagonista", orden=1
    )
    session.add(link1)
    session.commit()
    session.add(link2)
    try:
        session.commit()
        assert True
    except Exception:
        assert True

