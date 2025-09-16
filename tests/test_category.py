import pytest
from app.schemas.category import CreateCategory
from app.routers.category import create_category
from fastapi import HTTPException


class FakeDB:
    def __init__(self):
        self.executed = False
        self.committed = False

    async def execute(self, query):
        self.executed = True

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_create_category_as_admin(monkeypatch):
    fake_db = FakeDB()
    fake_user = {"is_admin": True}
    category_data = CreateCategory(name="Ноутбуки", parent_id=None)

    result = await create_category(fake_db, category_data, fake_user)

    assert result["status_code"] == 201
    assert result["transaction"] == "Successful"


@pytest.mark.asyncio
async def test_create_category_as_customer():
    fake_db = FakeDB()
    fake_user = {"is_admin": False}
    category_data = CreateCategory(name="Ноутбуки", parent_id=None)

    with pytest.raises(HTTPException) as exc:
        await create_category(fake_db, category_data, fake_user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "You must be admin user for this"


@pytest.mark.asyncio
async def test_create_category_by_admin(client, db_session, test_user_admin):

    login_data = {
        "username": test_user_admin["username"],
        "password": test_user_admin["password"]  # пароль в фикстуре хранится в чистом виде
    }
    login_resp = await client.post("/auth/token", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    category_data = {
        "name": "Ноутбуки",
    }
    category_resp = await client.post("/categories/", json=category_data,
                                                      headers={"Authorization": f"Bearer {token}"})
    category_resp_data = category_resp.json()

    assert category_resp.status_code == 201
    assert category_resp_data["transaction"] == 'Successful'

@pytest.mark.asyncio
async def test_create_category_by_customer(client, db_session, test_user):

    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]  # пароль в фикстуре хранится в чистом виде
    }
    login_resp = await client.post("/auth/token", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    category_data = {
        "name": "Ноутбуки",
    }
    category_resp = await client.post("/categories/", json=category_data,
                                                      headers={"Authorization": f"Bearer {token}"})
    category_resp_data = category_resp.json()

    assert category_resp.status_code == 403
    assert category_resp_data["detail"] == "You must be admin user for this"

