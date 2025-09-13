from .movie import Movie
from .genre import Genre
from .ratings import Review
from .recommendations import RecommendationResponse
from .real_person import RealPerson
from .movie_payload import Movie as PydanticMovie
from .platform import Platform
from .links import CastLink, MovieGenreLink, MoviePlatformLink

__all__ = [
    "Movie",
    "MovieGenreLink",
    "Genre",
    "Review",
    "RecommendationResponse",
    "MoviePlatformLink",
    "CastLink",
    "RealPerson",
    "PydanticMovie",
    "Platform",
]
