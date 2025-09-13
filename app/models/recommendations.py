from pydantic import BaseModel, ConfigDict
from app.models import Movie


class RecommendationResponse(BaseModel):
    movie: Movie
    score: float

    model_config = ConfigDict(from_attributes=True)
