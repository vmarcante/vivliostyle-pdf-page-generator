import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
