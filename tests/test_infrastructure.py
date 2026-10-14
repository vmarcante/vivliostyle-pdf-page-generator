from pathlib import Path
import asyncio

import pytest

from app.infrastructure.workdir import TempWorkspace
from app.infrastructure.vivlio import generate_config, run_cli, build_demo_project


def test_temp_workspace_context_manager():
    """O context manager deve fornecer o workspace e limpar ao sair."""
    with TempWorkspace() as ws:
        assert ws.path.exists()
        items = [("src/cover.html", b"<html><body>ok</body></html>")]
        saved = ws.write_items(items)
        assert len(saved) == 1
        assert saved[0].exists()
        assert saved[0].read_bytes() == items[0][1]
    # Após o `with`, o diretório deve ter sido removido
    assert not ws.path.exists()


def test_write_items_blocks_path_traversal():
    """Caminhos que tentam escapar do workspace devem ser redirecionados."""
    with TempWorkspace() as ws:
        items = [
            ("../../evil.txt", b"evil"),
            ("subdir/../../../escape.txt", b"escape"),
        ]
        saved = ws.write_items(items)
        workspace = ws.path.resolve()
        for p in saved:
            # Todos os arquivos devem estar dentro do workspace
            p.relative_to(workspace)  # levanta ValueError se escapar


def test_generate_config_creates_file(tmp_path: Path):
    src = tmp_path / "src"
    styles = tmp_path / "styles"
    src.mkdir()
    styles.mkdir()
    (src / "cover.html").write_text("<html></html>", encoding="utf-8")
    (src / "page.html").write_text("<html></html>", encoding="utf-8")
    (styles / "theme.css").write_text("body{}", encoding="utf-8")

    cfg = generate_config(tmp_path)

    assert cfg.exists()
    text = cfg.read_text(encoding="utf-8")
    # deve referenciar cover, page e o tema
    assert "cover.html" in text
    assert "page.html" in text
    assert "theme.css" in text


def test_generate_config_cover_comes_first(tmp_path: Path):
    """cover.html deve sempre ser o primeiro entry no config."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "aaa.html").write_text("<html></html>", encoding="utf-8")
    (src / "cover.html").write_text("<html></html>", encoding="utf-8")

    cfg = generate_config(tmp_path)
    text = cfg.read_text(encoding="utf-8")

    assert text.index("cover.html") < text.index("aaa.html")


def test_generate_config_falls_back_to_root_html(tmp_path: Path):
    # sem diretório src, deve usar HTMLs na raiz
    (tmp_path / "root.html").write_text("<html></html>", encoding="utf-8")

    cfg = generate_config(tmp_path)

    text = cfg.read_text(encoding="utf-8")
    assert "root.html" in text


async def test_run_cli_raises_on_nonzero_exit(tmp_path: Path, monkeypatch):
    async def fake_subprocess_exec(*cmd, **kwargs):
        class DummyProc:
            def __init__(self):
                self.returncode = 1

            async def communicate(self):  # type: ignore[override]
                return (b"error", None)

        return DummyProc()

    monkeypatch.setattr("app.infrastructure.vivlio.asyncio.create_subprocess_exec", fake_subprocess_exec)

    cfg = tmp_path / "vivliostyle.config.js"
    cfg.write_text("cfg", encoding="utf-8")
    out_pdf = tmp_path / "out.pdf"

    with pytest.raises(RuntimeError, match="Vivliostyle falhou"):
        await run_cli(tmp_path, cfg, out_pdf)


async def test_run_cli_raises_on_timeout(tmp_path: Path, monkeypatch):
    async def fake_subprocess_exec(*cmd, **kwargs):
        class SlowProc:
            def __init__(self):
                self.returncode = None

            async def communicate(self):
                await asyncio.sleep(9999)
                return (b"", None)

            def kill(self):
                pass

            async def wait(self):
                pass

        return SlowProc()

    monkeypatch.setattr("app.infrastructure.vivlio.asyncio.create_subprocess_exec", fake_subprocess_exec)
    monkeypatch.setattr("app.infrastructure.vivlio._VIVLIO_TIMEOUT", 0.01)

    cfg = tmp_path / "vivliostyle.config.js"
    cfg.write_text("cfg", encoding="utf-8")
    out_pdf = tmp_path / "out.pdf"

    with pytest.raises(RuntimeError, match="tempo limite"):
        await run_cli(tmp_path, cfg, out_pdf)


def test_build_demo_project_creates_files(tmp_path: Path):
    build_demo_project(tmp_path)

    assert (tmp_path / "styles" / "base.css").exists()
    assert (tmp_path / "styles" / "print.css").exists()
    assert (tmp_path / "src" / "cover.html").exists()


def test_build_demo_project_no_google_fonts(tmp_path: Path):
    """Demo não deve depender de rede externa."""
    build_demo_project(tmp_path)

    base_css = (tmp_path / "styles" / "base.css").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in base_css
