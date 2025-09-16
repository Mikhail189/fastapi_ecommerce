import pytest
from sqlalchemy import select
from app.models.user import User


@pytest.mark.asyncio
async def test_supplier_permission(client, test_user, db_session, test_user_admin):
    # 1. Логинимся под админом и получаем токен
    login_data = {
        "username": test_user_admin["username"],
        "password": test_user_admin["password"]  # пароль в фикстуре хранится в чистом виде
    }
    login_resp = await client.post("/auth/token", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    result = await db_session.execute(
        select(User).where(User.username == test_user["username"])
    )
    target_user = result.scalar_one()

    # 2. Делаем PATCH на смену роли (теперь токен нужен!)
    resp = await client.patch(
        "/permission/",
        params={"user_id": target_user.id},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["detail"] in ["User is now supplier", "User is no longer supplier"]

    # 3. Проверяем в базе, что роль изменилась
    await db_session.refresh(target_user)

    assert target_user.is_supplier is True
    assert target_user.is_customer is False


@pytest.mark.asyncio
async def test_delete_user(client, test_user, db_session, test_user_admin):
    # 1. Логинимся под админом и получаем токен
    login_data = {
        "username": test_user_admin["username"],
        "password": test_user_admin["password"]  # пароль в фикстуре хранится в чистом виде
    }
    login_resp = await client.post("/auth/token", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    result = await db_session.execute(
        select(User).where(User.username == test_user["username"])
    )
    target_user = result.scalar_one()

    # 2. Делаем PATCH на смену роли (теперь токен нужен!)
    resp = await client.delete(
        "/permission/delete",
        params={"user_id": target_user.id},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["detail"] in ["User has already been deleted", "User is deleted"]

    # 3. Проверяем в базе, что роль изменилась
    await db_session.refresh(target_user)

    assert target_user.is_active is False
