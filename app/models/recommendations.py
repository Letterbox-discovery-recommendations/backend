from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List
from app.models import Movie


class RecommendationResponse(BaseModel):
    movie: Movie
    score: float

    model_config = ConfigDict(from_attributes=True)


class GroupRecommendationRequest(BaseModel):
    """Request body para recomendaciones grupales."""
    user_ids: List[int] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Lista de IDs de usuarios del grupo (mínimo 2, máximo 10)"
    )
    
    @field_validator('user_ids')
    @classmethod
    def validate_unique_users(cls, v: List[int]) -> List[int]:
        """Validar que no haya IDs duplicados."""
        if len(v) != len(set(v)):
            raise ValueError("Los IDs de usuario no pueden estar duplicados")
        return v
