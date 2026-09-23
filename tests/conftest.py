import pytest
from fastapi.testclient import TestClient
from collections.abc import Generator
from typing import Any
###
from adeeb_fastapi.main import app


# client = TestClient(app, backend="asyncio")
# ASYNC_TRANSPORT = ASGITransport(app=app)
BASE_URL = "http://localhost:8000"


@pytest.fixture
def client()  -> Generator[TestClient, Any, None]:
    with TestClient(app=app, base_url=BASE_URL, backend="asyncio") as c:
        yield c


# # Couldn't configure it to use Async client.
# @pytest.fixture
# @pytest.mark.asyncio
# def async_client(client: TestClient) :
#     async def inner(client: TestClient):
#         async with AsyncClient(
#             transport=ASGITransport(client), base_url=BASE_URL  # pyright: ignore[reportArgumentType]
#         ) as ac:
#             yield ac
    
#     yield inner(client)