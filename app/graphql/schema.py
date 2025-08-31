import strawberry
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models import Movie, Actor, Genre
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

@strawberry.type
class GenreType:
    id: int
    name: str

    @strawberry.field
    def movies(self) -> List["MovieType"]:
        return self.movies # type: ignore

@strawberry.type
class MovieType:
    id: int
    title: str
    description: str
    release_year: int
    director: str
    duration: int
    
    @strawberry.field
    def cast(self) -> List[ActorType]:
        return self.cast # type: ignore
        
    @strawberry.field
    def genres(self) -> List[GenreType]:
        return self.genres # type: ignore



@strawberry.type
class Query:
    @strawberry.field
    def movies(self, title: Optional[str] = None) -> List["MovieType"]:
        """Obtiene una lista de películas, opcionalmente filtrada por título."""
        db_session: Session = next(get_session())
        

        statement = select(Movie).options(
            selectinload(Movie.cast),  # type: ignore
            selectinload(Movie.genres) # type: ignore
        )
        if title:
            statement = statement.where(Movie.title.contains(title)) # type: ignore
        
        results = db_session.exec(statement).all()
        db_session.close()
        return results # type: ignore

    @strawberry.field
    def actors(self, name: Optional[str] = None) -> List["ActorType"]:
        """Obtiene una lista de actores, opcionalmente filtrada por nombre."""
        db_session: Session = next(get_session())
        
        statement = select(Actor).options(selectinload(Actor.movies)) # type: ignore
        if name:
            statement = statement.where(Actor.name.contains(name)) # type: ignore
            
        results = db_session.exec(statement).all()
        db_session.close()
        return results # type: ignore


schema = strawberry.Schema(query=Query)