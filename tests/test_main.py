import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from collections.abc import AsyncGenerator, Generator
from typing import Any 
###
from adeeb_fastapi.main import app


client = TestClient(app, backend="asyncio")
ASYNC_TRANSPORT = ASGITransport(app=app)
BASE_URL = "http://localhost:8000"



def test_sync_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

@pytest.mark.asyncio
async def test_async_ping():
    async with AsyncClient(transport=ASYNC_TRANSPORT, base_url=BASE_URL) as client:
        response = await client.get(url="/ping")
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}


