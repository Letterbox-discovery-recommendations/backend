from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import List
from app.models import Movie


class RecommendationResponse(BaseModel):
    movie: Movie
    score: float

    model_config = ConfigDict(from_attributes=True)


class GroupRecommendationRequest(BaseModel):
    """Request body para recomendaciones grupales."""
    user_ids: List[int] = Field(
        default=None,
        min_length=2,
        max_length=10,
        description="Lista de IDs de usuarios del grupo (mínimo 2, máximo 10)"
    )
    base_user_id: int = Field(
        default=None,
        description="ID del usuario base para crear grupo automáticamente con sus seguidores"
    )
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v: List[int]) -> List[int]:
        """Validar que no haya IDs duplicados en user_ids."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Los IDs de usuario no pueden estar duplicados")
        return v
    
    @model_validator(mode='after')
    def validate_request_type(self):
        """Validar que se proporcione exactamente uno de los dos tipos de request."""
        has_user_ids = self.user_ids is not None
        has_base_user = self.base_user_id is not None
        
        if not has_user_ids and not has_base_user:
            raise ValueError("Debe proporcionar 'user_ids' o 'base_user_id'")
        
        if has_user_ids and has_base_user:
            raise ValueError("No puede proporcionar ambos 'user_ids' y 'base_user_id' al mismo tiempo")
        
        return self
