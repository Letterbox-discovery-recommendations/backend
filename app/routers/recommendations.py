from typing import List
from fastapi import APIRouter, Depends, HTTPException

# NUEVO: Importar AsyncSession
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.utils import get_session
from app.models import RecommendationResponse, GroupRecommendationRequest, User
from app.security import get_current_user, TokenPayload

# Asumo que tu servicio está en 'app.services' o 'app.recommendations'
from app.services import Recommendations

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/content", response_model=List[RecommendationResponse])
async def get_content_recommendations(
    # NUEVO: AsyncSession
    db_session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    recommendations = await engine.get_recommendations(current_user.user_id)
    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response


@router.get("/collaborative", response_model=List[RecommendationResponse])
async def get_collaborative_recommendations(
    # NUEVO: AsyncSession
    db_session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    recommendations = await engine.get_collaborative_recommendations(
        current_user.user_id
    )

    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response


@router.get("/similar/{movie_id}", response_model=List[RecommendationResponse])
async def get_similar_movies(
    movie_id: int,
    limit: int = 10,
    # NUEVO: AsyncSession
    db_session: AsyncSession = Depends(get_session),
):
    """
    Obtiene películas similares a una película específica basadas en metadatos.
    ...
    """
    limit = min(limit, 50)
    engine = Recommendations(db_session)

    # NUEVO: 'await'
    recommendations = await engine.get_similar_movies_by_metadata(movie_id, limit)

    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response


@router.get("/friends", response_model=List[User])
async def get_friends(
    # NUEVO: AsyncSession
    db_session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Obtiene la lista de amigos (seguidores mutuos) del usuario autenticado.
    ...
    """
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    friends = await engine.get_followed(current_user.user_id)

    return friends


@router.post("/group", response_model=List[RecommendationResponse])
async def get_group_recommendations(
    request: GroupRecommendationRequest,
    # NUEVO: AsyncSession
    db_session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Obtiene recomendaciones grupales combinando las preferencias de múltiples usuarios.
    ...
    """
    engine = Recommendations(db_session)

    try:
        if request.user_ids is not None:
            users_list = request.user_ids + [current_user.user_id]
            # NUEVO: 'await'
            recommendations = await engine.get_group_recommendations(users_list)

        else:
            raise HTTPException(status_code=400, detail="Método de request no válido")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response