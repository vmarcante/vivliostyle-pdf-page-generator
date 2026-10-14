import pytest

from app.presentation import routes


class DummyService:
    async def render_from_items(self, items):
        assert items  # deve receber ao menos um item
        return b"%PDF-1.4 dummy pdf bytes"

    async def render_demo(self):
        return b"%PDF-1.4 demo pdf bytes"


@pytest.fixture(autouse=True)
def override_service(monkeypatch):
    monkeypatch.setattr(routes, "service", DummyService())


@pytest.mark.asyncio
async def test_render_returns_pdf(client):
    files = {
        "src/cover.html": ("cover.html", b"<html><body>demo</body></html>", "text/html"),
    }
    response = await client.post("/render", files=files)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    content = await response.aread()
    assert content.startswith(b"%PDF-1.4")


@pytest.mark.asyncio
async def test_render_requires_files(client):
    response = await client.post("/render", files={})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_render_demo_returns_pdf(client):
    response = await client.post("/render/demo")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    content = await response.aread()
    assert content.startswith(b"%PDF-1.4")


@pytest.mark.asyncio
async def test_render_ignores_non_file_fields(client):
    # envia um campo de texto normal (não arquivo) para acionar o except/continue
    response = await client.post("/render", data={"foo": "bar"})
    # nenhum arquivo válido -> mesma validação de 400
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_render_runtime_error_returns_422(client, monkeypatch):
    """RuntimeError do serviço deve resultar em 422 com detalhe legível."""

    class FailingService:
        async def render_from_items(self, items):
            raise RuntimeError("Vivliostyle failed (exit 1)")

        async def render_demo(self):
            raise RuntimeError("Demo failed")

    monkeypatch.setattr(routes, "service", FailingService())

    files = {"src/cover.html": ("cover.html", b"<html></html>", "text/html")}
    response = await client.post("/render", files=files)
    assert response.status_code == 422
    assert "Vivliostyle failed" in response.json()["detail"]
