import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from app.models.movie import Movie
from app.models.genre import Genre, MovieGenreLink


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_and_query_actor(session):
    """
    Crea un actor, lo guarda y lo recupera. Valida todos los atributos.
    """
    actor = Actor(name="Test Actor", age=30, gender="M")
    session.add(actor)
    session.commit()
    from sqlmodel import select

    result = session.exec(select(Actor)).first()
    assert result.name == "Test Actor"
    assert result.age == 30
    assert result.gender == "M"
    assert result.id is not None


def test_create_actor_invalid_data(session):
    """
    Intenta crear un actor sin nombre (debe fallar por restricción NOT NULL).
    """
    with pytest.raises(Exception):
        actor = Actor(age=25, gender="F")
        session.add(actor)
        session.commit()


def test_create_and_query_movie(session):
    """
    Crea una película, la guarda y la recupera. Valida todos los atributos.
    """
    movie = Movie(
        title="Test Movie",
        description="Desc",
        release_year=2022,
        director="Dir",
        duration=90,
    )
    session.add(movie)
    result = session.exec(select(Movie)).first()
    assert result.title == "Test Movie"
    assert result.description == "Desc"
    assert result.release_year == 2022
    assert result.director == "Dir"
    assert result.duration == 90
    assert result.id is not None


def test_movie_actor_relationship(session):
    """
    Relaciona un actor y una película, y valida la relación desde ambos lados.
    """
    actor = Actor(name="Actor", age=40, gender="F")
    movie = Movie(
        title="Movie",
        description="Desc",
        release_year=2022,
        director="Dir",
        duration=90,
    )
    session.add(actor)
    session.add(movie)
    session.commit()
    link = MovieActorLink(movie_id=movie.id, actor_id=actor.id)
    session.add(link)
    session.commit()
    movie_from_db = session.get(Movie, movie.id)
    actor_from_db = session.get(Actor, actor.id)
    assert actor in movie_from_db.cast
    assert movie in actor_from_db.movies


def test_create_and_query_genre(session):
    """
    Crea un género, lo guarda y lo recupera. Valida todos los atributos.
    """
    genre = Genre(name="Action", description="Action desc")
    session.add(genre)
    result = session.exec(select(Genre)).first()
    result = session.exec(select(Genre)).first()
    assert result.name == "Action"
    assert result.id is not None


def test_movie_genre_relationship(session):
    """
    Relaciona una película y un género, y valida la relación desde ambos lados.
    """
    genre = Genre(name="Action", description="Action desc")
    movie = Movie(
        title="Movie2",
        description="Desc2",
        release_year=2023,
        director="Dir2",
        duration=100,
    )
    session.add(genre)
    session.add(movie)
    session.commit()
    link = MovieGenreLink(movie_id=movie.id, genre_id=genre.id)
    session.add(link)
    session.commit()
    movie_from_db = session.get(Movie, movie.id)
    genre_from_db = session.get(Genre, genre.id)
    assert genre in movie_from_db.genres
    assert movie in genre_from_db.movies


def test_delete_actor(session):
    """
    Crea y elimina un actor, comprobando que desaparece de la base de datos.
    """
    actor = Actor(name="ToDelete", age=50, gender="M")
    session.add(actor)
    session.commit()
    actor_id = actor.id
    session.delete(actor)
    session.commit()
    assert session.get(Actor, actor_id) is None


def test_update_movie(session):
    """
    Crea una película y actualiza sus atributos, validando el cambio.
    """
    movie = Movie(
        title="Old Title",
        description="Old",
        release_year=2000,
        director="A",
        duration=100,
    )
    session.add(movie)
    session.commit()
    movie.title = "New Title"
    movie.duration = 120
    session.add(movie)
    session.commit()
    updated = session.get(Movie, movie.id)
    assert updated.title == "New Title"
    assert updated.duration == 120
