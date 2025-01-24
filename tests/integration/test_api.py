import pytest
from httpx import AsyncClient
from clarity.main import app
from clarity.core.database import get_async_session
from clarity.models.user import User
from clarity.utils.crypto.hashing import hash_password

@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_user(test_db):
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    return user

async def test_user_login(test_client, test_user):
    response = await test_client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

async def test_get_insights(test_client, test_user, test_token):
    response = await test_client.get(
        "/api/v1/insights",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
