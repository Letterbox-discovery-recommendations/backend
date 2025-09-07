from pydantic import BaseModel
from app.models import Movie

class RecommendationResponse(BaseModel):
    movie: Movie
    score: float

    class Config:
        from_attributes = True