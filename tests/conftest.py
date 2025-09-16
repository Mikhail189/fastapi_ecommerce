# conftest.py
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.backend.db import Base
from app.backend.db_depends import get_db
from app.config import TEST_DATABASE_URL
from app.main import app
from sqlalchemy import update
from app.models.user import User

# --- Глобальный event loop (фикс для asyncpg + Windows) ---
@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на всю сессию тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# --- Создаём движок и фабрику сессий для тестовой базы ---
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


# --- Фикстура: чистая база на каждый тест ---
@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


# --- Фикстура: отдельная сессия для теста ---
@pytest_asyncio.fixture()
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


# --- Подмена зависимости get_db ---
@pytest.fixture(scope="function", autouse=True)
def override_dependency():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db


# --- HTTPX клиент через ASGITransport ---
@pytest_asyncio.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def test_user(client, db_session):
    """Создаёт тестового пользователя через API и возвращает объект User"""
    user_data = {
        "first_name": "Login",
        "last_name": "Tester",
        "username": "logintest",
        "email": "login@example.com",
        "password": "password123"
    }
    await client.post("/auth/", json=user_data)
    return user_data

@pytest_asyncio.fixture
async def test_user_admin(client, db_session):
    """Создаёт тестового пользователя через API и возвращает объект User"""
    user_data = {
        "first_name": "Admin",
        "last_name": "Tester",
        "username": "admintest",
        "email": "admin@example.com",
        "password": "password123"
    }
    await client.post("/auth/", json=user_data)

    await db_session.execute(
        update(User)
        .where(User.username == user_data["username"])
        .values(is_admin=True, is_customer=False)
    )
    await db_session.commit()
    #await db_session.refresh(user_data)

    return user_data

