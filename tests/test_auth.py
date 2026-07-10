from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import jwt
from app.config import settings
from fastapi import HTTPException

from app.api import deps
from app.api.v1.endpoints import auth as auth_endpoint
from app.main import app
from app.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)


class TestAuthService:
    def test_hash_and_verify_password_roundtrip(self):
        plain_password = "secret123"

        hashed_password = hash_password(plain_password)

        assert hashed_password != plain_password
        assert verify_password(plain_password, hashed_password)
        assert not verify_password("otra-clave", hashed_password)

    def test_create_access_token_can_be_validated(self):
        email = "admin@test.com"

        token = create_access_token(email)
        current_user = deps.get_current_user(token)

        assert isinstance(token, str)
        assert current_user == email

    def test_get_current_user_raises_401_when_token_is_invalid(self):
        with pytest.raises(HTTPException) as error:
            deps.get_current_user("token-invalido")

        assert error.value.status_code == 401
        assert error.value.detail == "Token inválido o expirado"

    def test_get_current_user_raises_401_when_token_has_no_sub(self):
        token = jwt.encode({}, settings.secret_key, algorithm="HS256")

        with pytest.raises(HTTPException) as error:
            deps.get_current_user(token)

        assert error.value.status_code == 401
        assert error.value.detail == "Token inválido"


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_returns_token_when_credentials_are_valid(self):
        email = "admin@test.com"
        password = "secret123"

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(
            return_value={
                "email": email,
                "hashed_password": hash_password(password),
            }
        )

        mock_database = {"users": mock_collection}

        transport = httpx.ASGITransport(app=app)

        with patch.object(auth_endpoint, "database", mock_database):
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/auth/login",
                    data={
                        "username": email,
                        "password": password,
                    },
                )

        assert response.status_code == 200

        response_data = response.json()

        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"

        mock_collection.find_one.assert_awaited_once_with(
            {"email": email}
        )

    @pytest.mark.asyncio
    async def test_login_returns_401_when_password_is_invalid(self):
        email = "admin@test.com"

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(
            return_value={
                "email": email,
                "hashed_password": hash_password("correct-password"),
            }
        )

        mock_database = {"users": mock_collection}

        transport = httpx.ASGITransport(app=app)

        with patch.object(auth_endpoint, "database", mock_database):
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/auth/login",
                    data={
                        "username": email,
                        "password": "wrong-password",
                    },
                )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Credenciales inválidas"
        }

    @pytest.mark.asyncio
    async def test_login_returns_401_when_user_does_not_exist(self):
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)

        mock_database = {"users": mock_collection}

        transport = httpx.ASGITransport(app=app)

        with patch.object(auth_endpoint, "database", mock_database):
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/auth/login",
                    data={
                        "username": "unknown@test.com",
                        "password": "secret123",
                    },
                )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Credenciales inválidas"
        }

    @pytest.mark.asyncio
    async def test_get_vehicles_returns_401_without_token(self):
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/vehicles")

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Not authenticated"
        }