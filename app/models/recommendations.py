from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import List
from app.models import Movie


class RecommendationResponse(BaseModel):
    movie: Movie
    score: float

    model_config = ConfigDict(from_attributes=True)


class FriendResponse(BaseModel):
    """Respuesta para información de un amigo."""
    id: int
    nombre: str
    foto: str

    model_config = ConfigDict(from_attributes=True)


class GroupRecommendationRequest(BaseModel):
    """Request body para recomendaciones grupales."""
    user_ids: List[int] = Field(
        default=None,
        min_length=2,
        max_length=10,
        description="Lista de IDs de usuarios del grupo (mínimo 2, máximo 10)"
    )
    base_user_ids: List[int] = Field(
        default=None,
        min_length=1,
        max_length=5,
        description="Lista de IDs de usuarios base para crear grupo automáticamente con sus seguidores"
    )
    user_id: int = Field(
        default=None,
        description="ID del usuario que solicita las recomendaciones (debe ser el usuario autenticado)"
    )
    friend_ids: List[int] = Field(
        default=None,
        min_length=1,
        max_length=9,
        description="Lista de IDs de amigos para incluir en el grupo junto con el user_id"
    )
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v: List[int]) -> List[int]:
        """Validar que no haya IDs duplicados en user_ids."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Los IDs de usuario no pueden estar duplicados")
        return v
    
    @field_validator('base_user_ids')
    @classmethod
    def validate_base_user_ids(cls, v: List[int]) -> List[int]:
        """Validar que no haya IDs duplicados en base_user_ids."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Los IDs de usuario base no pueden estar duplicados")
        return v
    
    @field_validator('friend_ids')
    @classmethod
    def validate_friend_ids(cls, v: List[int]) -> List[int]:
        """Validar que no haya IDs duplicados en friend_ids."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Los IDs de amigos no pueden estar duplicados")
        return v
    
    @model_validator(mode='after')
    def validate_request_type(self):
        """Validar que se proporcione exactamente uno de los tipos de request."""
        has_user_ids = self.user_ids is not None
        has_base_user_ids = self.base_user_ids is not None
        has_user_id_and_friends = self.user_id is not None and self.friend_ids is not None
        
        provided_methods = sum([has_user_ids, has_base_user_ids, has_user_id_and_friends])
        
        if provided_methods == 0:
            raise ValueError("Debe proporcionar 'user_ids', 'base_user_ids', o 'user_id' con 'friend_ids'")
        
        if provided_methods > 1:
            raise ValueError("Solo puede usar un método a la vez: 'user_ids', 'base_user_ids', o 'user_id'+'friend_ids'")
        
        return self
