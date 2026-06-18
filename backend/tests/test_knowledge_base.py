"""Knowledge Base API tests."""
import pytest
from httpx import AsyncClient


async def get_auth_header(client: AsyncClient, user_data: dict) -> dict:
    reg = await client.post("/api/v1/auth/register", json=user_data)
    if reg.status_code != 201:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]},
        )
        token = login.json()["access_token"]
    else:
        token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_knowledge_base(client: AsyncClient, user_data: dict, kb_data: dict):
    headers = await get_auth_header(client, user_data)
    response = await client.post("/api/v1/knowledge-bases/", json=kb_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == kb_data["name"]
    assert data["document_count"] == 0


@pytest.mark.asyncio
async def test_list_knowledge_bases(client: AsyncClient, user_data: dict, kb_data: dict):
    headers = await get_auth_header(client, user_data)
    await client.post("/api/v1/knowledge-bases/", json=kb_data, headers=headers)
    response = await client.get("/api/v1/knowledge-bases/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_knowledge_base(client: AsyncClient, user_data: dict, kb_data: dict):
    headers = await get_auth_header(client, user_data)
    create = await client.post("/api/v1/knowledge-bases/", json=kb_data, headers=headers)
    kb_id = create.json()["id"]
    response = await client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == kb_id


@pytest.mark.asyncio
async def test_update_knowledge_base(client: AsyncClient, user_data: dict, kb_data: dict):
    headers = await get_auth_header(client, user_data)
    create = await client.post("/api/v1/knowledge-bases/", json=kb_data, headers=headers)
    kb_id = create.json()["id"]
    response = await client.put(
        f"/api/v1/knowledge-bases/{kb_id}",
        json={"name": "Updated KB"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated KB"


@pytest.mark.asyncio
async def test_delete_knowledge_base(client: AsyncClient, user_data: dict, kb_data: dict):
    headers = await get_auth_header(client, user_data)
    create = await client.post("/api/v1/knowledge-bases/", json=kb_data, headers=headers)
    kb_id = create.json()["id"]
    response = await client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_kb_not_found(client: AsyncClient, user_data: dict):
    headers = await get_auth_header(client, user_data)
    import uuid
    response = await client.get(f"/api/v1/knowledge-bases/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404
