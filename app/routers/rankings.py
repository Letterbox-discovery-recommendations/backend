from typing import List
from fastapi import APIRouter, Depends

# NUEVO: Importar AsyncSession en lugar de Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.utils import get_session
from app.models import RecommendationResponse

# NUEVO: Asumo que tu servicio de recomendaciones está en app.services
# o donde lo hayas guardado (app.recommendations o similar)
from app.services import Recommendations
# from app.recommendations import Recommendations # <-- O esta, si se llama así

router = APIRouter(prefix="/api/v1/rankings", tags=["rankings"])


@router.get("/global", response_model=List[RecommendationResponse])
async def get_global_rankings(
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session) # NUEVO: AsyncSession
):
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    rankings = await engine.get_global_rankings(limit)
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in rankings
    ]
    return response


@router.get("/viral", response_model=List[RecommendationResponse])
async def get_viral_rankings(
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session) # NUEVO: AsyncSession
):
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    rankings = await engine.get_viral_rankings(limit)
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in rankings
    ]
    return response


@router.get("/platform/{platform_id}", response_model=List[RecommendationResponse])
async def get_rankings_by_platform(
    platform_id: int,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session) # NUEVO: AsyncSession
):
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    rankings = await engine.get_rankings_by_platform(platform_id, limit)
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in rankings
    ]
    return response


@router.get("/genre/{genre_id}", response_model=List[RecommendationResponse])
async def get_rankings_by_genre(
    genre_id: int,
    limit: int = 10,
    db_session: AsyncSession = Depends(get_session) # NUEVO: AsyncSession
):
    engine = Recommendations(db_session)
    # NUEVO: 'await'
    rankings = await engine.get_rankings_by_genre(genre_id, limit)
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in rankings
    ]
    return response