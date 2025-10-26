from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.utils import get_session
from app.models import RecommendationResponse, GroupRecommendationRequest, Follow
from app.security import get_current_user, TokenPayload
from app.services import Recommendations

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/content", response_model=List[RecommendationResponse])
async def get_content_recommendations(db_session: Session = Depends(get_session),current_user: TokenPayload = Depends(get_current_user)):
    engine = Recommendations(db_session)
    recommendations = engine.get_recommendations(current_user.user_id)
    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response


@router.get("/collaborative", response_model=List[RecommendationResponse])
async def get_collaborative_recommendations(db_session: Session = Depends(get_session),current_user: TokenPayload = Depends(get_current_user)):
    engine = Recommendations(db_session)
    recommendations = engine.get_collaborative_recommendations(current_user.user_id)

    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response


@router.get("/similar/{movie_id}", response_model=List[RecommendationResponse])
async def get_similar_movies(
    movie_id: int,
    limit: int = 10,
    exclude_watched: bool = True,
db_session: Session = Depends(get_session),current_user: TokenPayload = Depends(get_current_user)
):
    """
    Obtiene películas similares a una película específica basadas en metadatos.
    
    Parámetros:
    - movie_id: ID de la película de referencia
    - limit: cantidad de recomendaciones (default 10, max 50)
    - exclude_watched: excluir películas ya vistas por el usuario
    
    Retorna: Lista de películas similares con score de similitud
    """
    limit = min(limit, 50)
    engine = Recommendations(db_session)
    
    user_id = current_user.user_id if exclude_watched else None
    recommendations = engine.get_similar_movies_by_metadata(movie_id, limit, user_id)
    
    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response


@router.get("/cowatch/{movie_id}", response_model=List[RecommendationResponse])
async def get_cowatch_recommendations(
    movie_id: int,
    limit: int = 10,
    db_session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Obtiene películas vistas conjuntamente: "Usuarios que vieron X también vieron Y".
    Basado en co-visualización y ratings positivos compartidos.

    Parámetros:
    - movie_id: ID de la película de referencia
    - limit: cantidad de recomendaciones (default 10, max 50)

    Retorna: Lista de películas con métrica de co-visualización como score
    """
    limit = min(limit, 50)
    engine = Recommendations(db_session)

    recommendations = engine.get_cowatch_recommendations(movie_id, limit)

    response = [
        RecommendationResponse(movie=item["movie"], score=item["support"])
        for item in recommendations
    ]
    return response


@router.get("/friends", response_model=List[int])
async def get_friends(
    db_session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Obtiene la lista de amigos (seguidores mutuos) del usuario autenticado.

    Un amigo es alguien que sigue al usuario Y el usuario lo sigue a él.

    Returns:
        Lista de IDs de amigos
    """
    engine = Recommendations(db_session)
    friends = engine.get_followed(current_user.user_id)

    return friends



@router.post("/group", response_model=List[RecommendationResponse])
async def get_group_recommendations(
    request: GroupRecommendationRequest,
    db_session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Obtiene recomendaciones grupales combinando las preferencias de múltiples usuarios.
    
    Se puede usar de tres formas:
    1. Proporcionar 'user_ids': Lista explícita de IDs de usuarios (2-10 usuarios)
    2. Proporcionar 'base_user_ids': Lista de IDs de usuarios base para crear grupo automáticamente con sus seguidores
    3. Proporcionar 'user_id' y 'friend_ids': Usuario solicitante + lista de amigos seleccionados
    
    - Requiere que el usuario autenticado esté incluido en el grupo
    - Combina perfiles individuales usando content-based y collaborative filtering
    - Pondera por actividad de cada usuario (número de reseñas)
    - Retorna películas que reflejan los intereses comunes del grupo
    """
    engine = Recommendations(db_session)
    
    try:
        if request.user_ids is not None:
            users_list = request.user_ids + [current_user.user_id]
            recommendations = engine.get_group_recommendations(users_list)

        else:
            raise HTTPException(status_code=400, detail="Método de request no válido")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response
