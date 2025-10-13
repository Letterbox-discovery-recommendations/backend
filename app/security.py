import time
from typing import Annotated, List, Dict, Optional
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from jose import jwt, JWTError
from starlette import status
from pydantic import BaseModel

JWKS_URL = os.getenv("JWKS_URL")

jwks_cache = {
    "keys": [],
    "expires_at": 0
}
CACHE_LIFETIME_SECONDS = 60 * 60 * 24

security_scheme = HTTPBearer()



class TokenPayload(BaseModel):
    sub: str
    exp: int
    user_id: int
    name: str
    last_name: str
    email: str
    role: str
    image_url: Optional[str] = None
    permissions: List[str] = []
    is_active: bool
    full_name: str


async def get_jwks() -> List[Dict]:
    """
    Obtiene las claves JWKS desde la URL, usando una caché en memoria para
    evitar peticiones HTTP constantes.
    """
    if jwks_cache["expires_at"] > time.time():
        return jwks_cache["keys"]


    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(JWKS_URL)
            response.raise_for_status()

            jwks = response.json()
            jwks_cache["keys"] = jwks.get("keys", [])
            jwks_cache["expires_at"] = time.time() + CACHE_LIFETIME_SECONDS

            return jwks_cache["keys"]

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo contactar al servicio de autenticación: {e}",
            )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
) -> TokenPayload:
    """
    Valida el token JWT usando la clave pública obtenida del JWKS endpoint.
    """
    token = credentials.credentials

    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise unauthorized_exception

        jwks_keys = await get_jwks()

        public_key = None
        for key in jwks_keys:
            if key["kid"] == kid:
                public_key = key
                break

        if not public_key:
            jwks_cache["expires_at"] = 0
            jwks_keys = await get_jwks()
            for key in jwks_keys:
                if key["kid"] == kid:
                    public_key = key
                    break

            if not public_key:
                raise unauthorized_exception


        payload = jwt.decode(token, public_key, algorithms=["RS256"])

        token_data = TokenPayload(**payload)
        return token_data

    except JWTError:
        raise unauthorized_exception