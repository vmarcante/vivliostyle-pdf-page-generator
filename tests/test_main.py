async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_root_redirects_to_docs(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "/docs" in response.headers.get("location", "")


async def test_oversized_content_length_returns_413(client):
    """Content-Length maior que o limite deve retornar 413 imediatamente."""
    from app.main import _MAX_REQUEST_SIZE

    response = await client.post(
        "/render",
        content=b"x",
        headers={"content-length": str(_MAX_REQUEST_SIZE + 1)},
    )
    assert response.status_code == 413


async def test_warmup_failure_does_not_crash_server(monkeypatch):
    """Falha no warmup não deve impedir o servidor de responder."""
    import pytest_asyncio
    from httpx import AsyncClient, ASGITransport
    from app.application import service as svc_module

    # Simula Vivliostyle indisponível
    async def failing_run_cli(*args, **kwargs):
        raise RuntimeError("vivliostyle não encontrado")

    monkeypatch.setattr(svc_module, "run_cli", failing_run_cli)

    from app.main import app as fastapi_app
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
