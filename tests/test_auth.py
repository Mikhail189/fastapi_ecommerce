import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.routers.auth import bcrypt_context
from app.models.user import User
from sqlalchemy import select
from app.routers.auth import authenticate_user, bcrypt_context

class FakeUser:
    def __init__(self):
        self.username = "testuser"
        self.hashed_password = "hashed"
        self.is_active = True


@pytest.mark.asyncio
async def test_authenticate_user_success(monkeypatch):
    fake_user = FakeUser()

    class FakeDB:
        async def scalar(self, query):
            return fake_user

    # мок без строкового пути
    monkeypatch.setattr(bcrypt_context, "verify", lambda pwd, hashed: True)

    result = await authenticate_user(FakeDB(), "testuser", "secret")
    assert result is fake_user


@pytest.mark.asyncio
async def test_create_user(client, db_session):
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "secret123"
    }

    resp = await client.post("/auth/", json=user_data)
    data = resp.json()

    assert resp.status_code == 201
    assert data["transaction"] == "Successful"

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()
    assert user.email == "test@example.com"
    assert user.last_name == "User"
    assert user.first_name == "Test"
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    # теперь пробуем логин
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    resp = await client.post("/auth/token", data=login_data)
    data = resp.json()

    assert resp.status_code == 200
    assert "access_token" in data
    assert data["token_type"] == "bearer"
