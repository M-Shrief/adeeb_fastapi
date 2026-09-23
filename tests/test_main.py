import pytest
from fastapi.testclient import TestClient
###
from adeeb_fastapi.main import app

# def general_mock():
#     # app.dependency_overrides[get_async_db] = general_mock
#     # app.dependency_overrides[get_async_cache] = general_mock
#     return "mock"

@pytest.mark.asyncio
async def test_index(client: TestClient):
    response = client.get(url="/")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == app.title
    assert body["description"] == app.description
    assert body["version"] == app.version
    assert body["Swagger-documentation_url"] == app.docs_url
    assert body["Redoc-documentation_url"] == app.redoc_url
    assert body["Scalar-documentation_url"] == "/scalar"
            # "title": app.title,
            # "description": app.description,
            # "version": app.version,
            # "Swagger-documentation_url": app.docs_url,
            # "Redoc-documentation_url": app.redoc_url,
            # "Scalar-documentation_url": "/scalar"            




@pytest.mark.asyncio
async def test_ping(client: TestClient):
    response = client.get(url="/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

