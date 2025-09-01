import strawberry
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models import Movie, Actor
from app.db.config import get_session


# Para evitar dependencias circulares al definir las relaciones,
# usamos strawberry.LazyType.
@strawberry.type
class ActorType:
    id: int
    name: str
    age: int
    gender: str

    # Resolver para obtener las películas de este actor
    @strawberry.field
    def movies(self) -> List["MovieType"]:
        return self.movies # type: ignore

    # Resolver para obtener en que años ha actuado este actor
    @strawberry.field
    def years_active(self) -> List[int]:
        return [movie.release_year for movie in self.movies] # type: ignore

@strawberry.type
class GenreType:
    id: int
    name: str

    # Resolver para obtener las películas de este género
    @strawberry.field
    def movies(self) -> List["MovieType"]:
        return self.movies  # type: ignore


@strawberry.type
class MovieType:
    id: int
    title: str
    description: str
    release_year: int
    director: str
    duration: int
    platform: str
    rating: float
    is_high_rated: bool



    # Resolver para obtener el elenco de esta película
    @strawberry.field
    def cast(self) -> List[ActorType]:
        return self.cast # type: ignore

    # Resolver para obtener los géneros de esta película
    @strawberry.field
    def genres(self) -> List[GenreType]:
        return self.genres # type: ignore

    # Resolver para obtener la plataforma de esta película
    @strawberry.field
    def platform(self) -> str:
        return self.platform # type: ignore

    # Resolver para obtener la calificación de esta película
    @strawberry.field
    def rating(self) -> float:
        return self.rating # type: ignore
    
    @strawberry.field
    def is_high_rated(self) -> bool:
        return self.rating >= 4.0 #type: ignore

@strawberry.type
class Query:
    @strawberry.field
    def movies(self, title: Optional[str] = None, platform: Optional[str] = None, max_rating: Optional[float] = None, min_rating: Optional[float] = None, min_year: Optional[int] = None, max_year: Optional[int] = None, genre: Optional[str] = None, min_duration: Optional[int] = None, max_duration: Optional[int] = None, limit: Optional[int] = None, sort: Optional[str] = None) -> List["MovieType"]:
        """Obtiene una lista de películas, opcionalmente filtrada por título y calificación mínima."""
        db_session: Session = next(get_session())
        
        # Validaciones
        if max_duration and min_duration and max_duration < min_duration:
            raise ValueError("La duración máxima no puede ser menor que la duración mínima.")
        if max_year and min_year and max_year < min_year:
            raise ValueError("El año máximo no puede ser menor que el año mínimo.")
        if min_rating and max_rating and max_rating < min_rating:
            raise ValueError("La calificación máxima no puede ser menor que la calificación mínima.")

        if limit and limit <= 0:
            raise ValueError("El límite debe ser mayor que 0.")

        if min_year and min_year < 1888:
            raise ValueError("El año mínimo no puede ser menor que 1888.")
        
    
        statement = select(Movie).options(
            selectinload(Movie.cast),  # type: ignore
            selectinload(Movie.genres),  # type: ignore
        )
        if title:
            statement = statement.where(Movie.title.contains(title)) # type: ignore

        if max_rating:
            statement = statement.where(Movie.rating <= max_rating) # type: ignore
        if min_rating:
            statement = statement.where(Movie.rating >= min_rating) # type: ignore
        if min_year:
            statement = statement.where(Movie.release_year >= min_year) # type: ignore
        if max_year:
            statement = statement.where(Movie.release_year <= max_year) # type: ignore
        if genre:
            statement = statement.where(Movie.genres.any(Genre.name == genre)) # type: ignore
        if max_duration:
            statement = statement.where(Movie.duration <= max_duration) # type: ignore
        if min_duration:
            statement = statement.where(Movie.duration >= min_duration) # type: ignore
        if platform:
            statement = statement.where(Movie.platform == platform) # type: ignore
        if limit:
            statement = statement.limit(limit) # type: ignore
        if sort:
            if sort == "year_desc":
                statement = statement.order_by(Movie.release_year.desc())  # Año descendente 
            elif sort == "year_asc":
                statement = statement.order_by(Movie.release_year.asc())  # Año ascendente
            elif sort == "duration_asc":
                statement = statement.order_by(Movie.duration.asc())  # Duración ascendente
            elif sort == "duration_desc":
                statement = statement.order_by(Movie.duration.desc())  # Duración descendente
            elif sort == "rating_desc":
                statement = statement.order_by(Movie.rating.desc())  # Rating descendente
            elif sort == "rating_asc":
                statement = statement.order_by(Movie.rating.asc())  # Rating ascendente
            elif sort == "title_asc":
                statement = statement.order_by(Movie.title.asc())  # Título ascendente
            elif sort == "title_desc":
                statement = statement.order_by(Movie.title.desc())  # Título descendente

        results = db_session.exec(statement).all()
        db_session.close()
        return results  # type: ignore

    @strawberry.field
    def actors(self, name: Optional[str] = None) -> List["ActorType"]:
        """Obtiene una lista de actores, opcionalmente filtrada por nombre."""
        db_session: Session = next(get_session())

        statement = select(Actor).options(selectinload(Actor.movies))  # type: ignore
        if name:
            statement = statement.where(Actor.name.contains(name))  # type: ignore

        results = db_session.exec(statement).all()
        db_session.close()
        return results # type: ignore
    
    @strawberry.field
    def genres(self, name: Optional[str] = None) -> List["GenreType"]:
        """Obtiene una lista de géneros, opcionalmente filtrada por nombre."""
        db_session: Session = next(get_session())
        
        statement = select(Genre).options(selectinload(Genre.movies))
        results = db_session.exec(statement).all()
        db_session.close()
        return results


schema = strawberry.Schema(query=Query)
