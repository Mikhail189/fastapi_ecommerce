import pytest
import httpx

BASE_URL = "http://localhost:8001"  # e2e-сервер


@pytest.mark.asyncio
async def test_register_and_login_e2e():
    async with httpx.AsyncClient(base_url=BASE_URL, trust_env=False) as client:
        # 1. регистрация
        user_data = {
            "first_name": "E2E",
            "last_name": "Tester",
            "username": "e2etest",
            "email": "e2e@example.com",
            "password": "secret123"
        }
        resp = await client.post("/auth/", json=user_data)
        print("Response:", resp.status_code, resp.text)
        assert resp.status_code == 201
        assert resp.json()["transaction"] == "Successful"

        # 2. логин
        login_data = {"username": "e2etest", "password": "secret123"}
        resp = await client.post("/auth/token", data=login_data)
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # 3. профиль
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get("/auth/read_current_user", headers=headers)
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["User"]["username"] == "e2etest"
