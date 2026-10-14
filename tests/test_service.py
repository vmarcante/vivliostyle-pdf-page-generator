import asyncio
from pathlib import Path

import pytest

from app.application.service import RenderService


class DummyWorkspace:
    def __init__(self, base: Path):
        self.path = base
        self.cleaned = False

    def write_items(self, items):
        paths = []
        for rel, data in items:
            p = self.path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            paths.append(p)
        return paths

    def cleanup(self):
        self.cleaned = True


@pytest.mark.asyncio
async def test_render_from_items_uses_existing_out_pdf(tmp_path, monkeypatch):
    ws = DummyWorkspace(tmp_path)
    out = tmp_path / "out.pdf"
    out.write_bytes(b"PDF")

    def fake_temp_workspace():
        return ws

    async def fake_run_cli(workdir, cfg, out_pdf):
        # não cria nada, usa o out.pdf já existente
        assert workdir == tmp_path

    def fake_generate_config(workdir):
        cfg = workdir / "vivliostyle.config.js"
        cfg.write_text("cfg", encoding="utf-8")
        return cfg

    monkeypatch.setattr("app.application.service.TempWorkspace", fake_temp_workspace)
    monkeypatch.setattr("app.application.service.run_cli", fake_run_cli)
    monkeypatch.setattr("app.application.service.generate_config", fake_generate_config)

    service = RenderService()
    pdf = await service.render_from_items([("src/cover.html", b"<html></html>")])

    assert pdf == b"PDF"
    assert ws.cleaned is True


@pytest.mark.asyncio
async def test_render_from_items_falls_back_to_first_pdf(tmp_path, monkeypatch):
    ws = DummyWorkspace(tmp_path)

    def fake_temp_workspace():
        return ws

    async def fake_run_cli(workdir, cfg, out_pdf):
        # Vivliostyle gera PDF em local não-padrão (não em out.pdf)
        new_pdf = workdir / "nested" / "other.pdf"
        new_pdf.parent.mkdir(parents=True, exist_ok=True)
        new_pdf.write_bytes(b"OTHER")

    def fake_generate_config(workdir):
        cfg = workdir / "vivliostyle.config.js"
        cfg.write_text("cfg", encoding="utf-8")
        return cfg

    monkeypatch.setattr("app.application.service.TempWorkspace", fake_temp_workspace)
    monkeypatch.setattr("app.application.service.run_cli", fake_run_cli)
    monkeypatch.setattr("app.application.service.generate_config", fake_generate_config)

    service = RenderService()
    pdf = await service.render_from_items([("src/cover.html", b"<html></html>")])

    assert pdf == b"OTHER"
    assert ws.cleaned is True


@pytest.mark.asyncio
async def test_render_from_items_does_not_return_preexisting_pdf(tmp_path, monkeypatch):
    """PDFs enviados pelo cliente não devem ser devolvidos como resultado."""
    ws = DummyWorkspace(tmp_path)
    # PDF enviado como parte do upload (pré-existente no workspace)
    preexisting = tmp_path / "uploaded.pdf"
    preexisting.write_bytes(b"UPLOADED")

    def fake_temp_workspace():
        return ws

    async def fake_run_cli(workdir, cfg, out_pdf):
        # Vivliostyle não gera nenhum PDF
        if out_pdf.exists():
            out_pdf.unlink()

    def fake_generate_config(workdir):
        cfg = workdir / "vivliostyle.config.js"
        cfg.write_text("cfg", encoding="utf-8")
        return cfg

    monkeypatch.setattr("app.application.service.TempWorkspace", fake_temp_workspace)
    monkeypatch.setattr("app.application.service.run_cli", fake_run_cli)
    monkeypatch.setattr("app.application.service.generate_config", fake_generate_config)

    service = RenderService()

    with pytest.raises(RuntimeError, match="PDF not generated"):
        await service.render_from_items([("uploaded.pdf", b"UPLOADED")])

    assert ws.cleaned is True


@pytest.mark.asyncio
async def test_render_from_items_raises_when_no_pdf(tmp_path, monkeypatch):
    ws = DummyWorkspace(tmp_path)

    def fake_temp_workspace():
        return ws

    async def fake_run_cli(workdir, cfg, out_pdf):
        # não cria nenhum PDF
        if out_pdf.exists():
            out_pdf.unlink()

    def fake_generate_config(workdir):
        cfg = workdir / "vivliostyle.config.js"
        cfg.write_text("cfg", encoding="utf-8")
        return cfg

    monkeypatch.setattr("app.application.service.TempWorkspace", fake_temp_workspace)
    monkeypatch.setattr("app.application.service.run_cli", fake_run_cli)
    monkeypatch.setattr("app.application.service.generate_config", fake_generate_config)

    service = RenderService()

    with pytest.raises(RuntimeError, match="PDF not generated"):
        await service.render_from_items([("src/cover.html", b"<html></html>")])

    assert ws.cleaned is True


@pytest.mark.asyncio
async def test_render_demo_uses_demo_project(tmp_path, monkeypatch):
    ws = DummyWorkspace(tmp_path)
    out = tmp_path / "out.pdf"

    def fake_temp_workspace():
        return ws

    def fake_build_demo_project(workdir):
        # cria arquivos de demo
        (workdir / "src").mkdir(parents=True, exist_ok=True)
        (workdir / "src" / "cover.html").write_text("demo", encoding="utf-8")

    def fake_generate_config(workdir):
        cfg = workdir / "vivliostyle.config.js"
        cfg.write_text("cfg", encoding="utf-8")
        return cfg

    async def fake_run_cli(workdir, cfg, out_pdf):
        out_pdf.write_bytes(b"DEMO")

    monkeypatch.setattr("app.application.service.TempWorkspace", fake_temp_workspace)
    monkeypatch.setattr("app.application.service.build_demo_project", fake_build_demo_project)
    monkeypatch.setattr("app.application.service.generate_config", fake_generate_config)
    monkeypatch.setattr("app.application.service.run_cli", fake_run_cli)

    service = RenderService()
    pdf = await service.render_demo()

    assert pdf == b"DEMO"
    assert ws.cleaned is True
