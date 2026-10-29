import pytest
from httpx import AsyncClient

#client endpiont test
@pytest.mark.asyncio
async def test_login_success(client:AsyncClient):
    payload={
        "username":"admin@example.com",
        "password":"StrongPassword123!"
    }

    response=await client.post("/auth/login",data=payload)

    assert response.status_code==200
    data=response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

#protected route test 
@pytest.mark.asyncio
async def test_protected_route_requires_auth(client:AsyncClient):
    response=await client.get("/users/me")

    assert response.status_code == 401

#token-authorized call:
@pytest.mark.asyncio
async def test_protected_route_with_token(client:AsyncClient):

    login =await client.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": "StrongPassword123!"}
    )

    token=login.json()["access_token"]

    response=await client.get(
        "/users/me",
        headers={"Authorization":f"Bearer {token}"}
    )
    
    assert response.status_code ==200