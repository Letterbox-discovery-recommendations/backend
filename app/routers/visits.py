import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from app.security import get_current_user, TokenPayload
import httpx
import os

router = APIRouter(prefix="/api/v1/visits", tags=["visits"])

class VisitedMovie(BaseModel):
    movie_id : int

class Response(BaseModel):
    message: str


@router.post("/visit", response_model=Response)
async def get_content_recommendations(visited_movie : VisitedMovie,current_user: TokenPayload = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{os.getenv('CORE_URL')}/events/receive?routingKey=discovery.pelicula.visitada",
                json={
                    "type": "discovery.pelicula.visitada",
                    "source": "/discovery/api",
                    "datacontenttype": "application/json",
                    "sysDate": datetime.datetime.now().isoformat(),
                    "data": {
                        "evento": "pelicula_visitada",
                        "movie_id": visited_movie.movie_id,
                        "user_id": current_user.user_id,
                    },
                },
            )
            response.raise_for_status()

            return Response(message="Visita registrada correctamente.")

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo contactar al servicio de autenticación: {e}",
            )

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"El servicio de core devolvió un error: {e.response.text}",
            )





