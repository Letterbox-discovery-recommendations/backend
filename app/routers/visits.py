import datetime
import json
import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
import httpx
import os
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.utils import get_session
from app.models import Mensaje
from app.security import get_current_user, TokenPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/visits", tags=["visits"])


class VisitedMovie(BaseModel):
    movie_id: int


class Response(BaseModel):
    message: str


@router.post("/visit", response_model=Response)
async def get_content_recommendations(
    visited_movie: VisitedMovie,
    current_user: TokenPayload = Depends(get_current_user),
    # NUEVO: Usar AsyncSession
    db_session: AsyncSession = Depends(get_session),
):
    # --- 1. Lógica de Base de Datos (Ahora Asíncrona) ---
    # Eliminamos run_in_threadpool y la función interna
    try:
        nuevo_mensaje = Mensaje(
            evento="discovery.pelicula.visitada",
            tipo="PUBLISH",
            # NOTA: No es necesario json.dumps si tu modelo usa 'dict' para 'data'
            # Pero si tu modelo 'Mensaje' espera un string, esto es correcto.
            data=json.dumps(
                {
                    "movie_id": visited_movie.movie_id,
                    "user_id": current_user.user_id,
                }
            ),
        )
        db_session.add(nuevo_mensaje)

        # NUEVO: Commit manual asíncrono
        # Esto guarda la visita ANTES de intentar la llamada HTTP
        await db_session.commit()

    except Exception as e:
        # NUEVO: Rollback asíncrono
        # (Aunque get_session ya lo hace, ser explícito aquí es bueno)
        await db_session.rollback()
        logger.error(f"Error crítico al registrar visita en DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error crítico al registrar la visita en la base de datos: {e}",
        )

    # --- 2. Lógica de Notificación HTTP (Sin cambios) ---
    # Esta parte ya era asíncrona y estaba correcta.
    json_payload = {
        "type": "discovery.pelicula.visitada",
        "source": "/discovery/api",
        "datacontenttype": "application/json",
        "sysDate": datetime.datetime.now().isoformat(),
        "data": {
            "evento": "pelicula_visitada",
            "movie_id": visited_movie.movie_id,
            "user_id": current_user.user_id,
        },
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{os.getenv('CORE_URL')}/events/receive?routingKey=discovery.pelicula.visitada",
                json=json_payload,
                headers={"X-API-KEY": os.getenv("CORE_API_KEY")},
            )
            response.raise_for_status()

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            # Esta lógica es correcta: la visita se guardó, solo falló la notificación.
            logger.warning(
                f"Visita registrada exitosamente (User: {current_user.user_id}, Movie: {visited_movie.movie_id}), "
                f"pero falló la notificación al servicio core: {e}"
            )

    return Response(message="Visita registrada correctamente.")