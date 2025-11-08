import datetime
import json
import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from app.db.utils import get_session
from app.models import Mensaje
from app.security import get_current_user, TokenPayload
import httpx
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/visits", tags=["visits"])

class VisitedMovie(BaseModel):
    movie_id : int

class Response(BaseModel):
    message: str


@router.post("/visit", response_model=Response)
async def get_content_recommendations(
    visited_movie: VisitedMovie,
    current_user: TokenPayload = Depends(get_current_user),
    db_session: Session = Depends(get_session),
):

    def save_visit_to_db():
        try:
            nuevo_mensaje = Mensaje(
                evento="discovery.pelicula.visitada",
                tipo="PUBLISH",
                data=json.dumps(
                    {
                        "movie_id": visited_movie.movie_id,
                        "user_id": current_user.user_id,
                    }
                ),
            )
            db_session.add(nuevo_mensaje)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e

    try:
        await run_in_threadpool(save_visit_to_db)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error crítico al registrar la visita en la base de datos: {e}",
        )


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
                json=json_payload,headers= { "X-API-KEY" : os.getenv("CORE_API_KEY")},
            )
            response.raise_for_status()

        except (httpx.RequestError, httpx.HTTPStatusError) as e:

            logger.warning(
                f"Visita registrada exitosamente (User: {current_user.user_id}, Movie: {visited_movie.movie_id}), "
                f"pero falló la notificación al servicio core: {e}"
            )

    return Response(message="Visita registrada correctamente.")