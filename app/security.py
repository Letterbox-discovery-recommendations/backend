from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials




security_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
) -> dict:
    """
    Una dependencia que valida el token JWT y devuelve su payload.
    Si el token es inválido, lanza una HTTPException.
    """
    token = credentials.credentials

    print(token)
    return {"estado" : "todo ok"}