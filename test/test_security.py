import asyncio
import time
import pytest
from unittest.mock import AsyncMock

import httpx
import app.security as security
from fastapi import HTTPException
from jose import JWTError


def test_get_jwks_success(monkeypatch):
    # Simular httpx.AsyncClient.get para devolver jwks
    fake_jwks = {"keys": [{"kid": "test-kid", "kty": "RSA", "use": "sig"}]}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return fake_jwks

    async def fake_get(self, url):
        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    # Asegurar cache vacío
    security.jwks_cache["keys"] = []
    security.jwks_cache["expires_at"] = 0

    keys = asyncio.run(security.get_jwks())
    assert isinstance(keys, list)
    assert keys == fake_jwks["keys"]


def test_get_jwks_cached(monkeypatch):
    # Poblar cache con expiración futura
    security.jwks_cache["keys"] = [{"kid": "cached"}]
    security.jwks_cache["expires_at"] = time.time() + 60

    keys = asyncio.run(security.get_jwks())
    assert keys == [{"kid": "cached"}]


def test_get_jwks_request_error(monkeypatch):
    async def fake_get_raise(self, url):
        raise httpx.RequestError("network error")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get_raise)

    security.jwks_cache["keys"] = []
    security.jwks_cache["expires_at"] = 0

    with pytest.raises(HTTPException) as exc:
        asyncio.run(security.get_jwks())

    assert exc.value.status_code == 503


def test_get_current_user_success(monkeypatch):
    # Preparar un token fake y parchear jwt functions y get_jwks
    fake_token = "header.payload.signature"
    fake_header = {"kid": "k1"}
    fake_payload = {
        "sub": "sub",
        "exp": 9999999999,
        "user_id": 1,
        "name": "Test",
        "last_name": "User",
        "email": "a@b.c",
        "role": "user",
        "permissions": [],
        "is_active": True,
        "full_name": "Test User",
    }

    monkeypatch.setattr(security, "get_jwks", AsyncMock(return_value=[{"kid": "k1", "n": "x"}]))
    # Patch jwt functions on the security.jwt module for robustness
    monkeypatch.setattr(security.jwt, "get_unverified_header", lambda token: fake_header)
    monkeypatch.setattr(security.jwt, "decode", lambda token, key, algorithms: fake_payload)

    # Construir objeto credentials con atributo credentials
    class C:
        pass

    creds = C()
    creds.credentials = fake_token

    user = asyncio.run(security.get_current_user(creds))
    assert user.user_id == 1
    assert user.email == "a@b.c"


def test_get_current_user_missing_kid(monkeypatch):
    fake_token = "t"
    monkeypatch.setattr(security.jwt, "get_unverified_header", lambda token: {})

    class C:
        pass

    creds = C()
    creds.credentials = fake_token

    with pytest.raises(HTTPException) as exc:
        asyncio.run(security.get_current_user(creds))

    assert exc.value.status_code == 401


def test_get_current_user_decode_error(monkeypatch):
    fake_token = "t"
    monkeypatch.setattr(security.jwt, "get_unverified_header", lambda token: {"kid": "k"})
    monkeypatch.setattr(security, "get_jwks", AsyncMock(return_value=[{"kid": "k"}]))

    def raise_jwt_error(token, key, algorithms):
        raise JWTError()

    monkeypatch.setattr(security.jwt, "decode", raise_jwt_error)

    class C:
        pass

    creds = C()
    creds.credentials = fake_token

    with pytest.raises(HTTPException) as exc:
        asyncio.run(security.get_current_user(creds))

    assert exc.value.status_code == 401
