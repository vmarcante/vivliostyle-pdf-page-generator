from pathlib import Path
from typing import Iterable, Tuple
import time
import logging

from app.infrastructure.workdir import TempWorkspace
from app.infrastructure.vivlio import generate_config, run_cli, build_demo_project

logger = logging.getLogger(__name__)


class RenderService:
    async def render_from_items(self, items: Iterable[Tuple[str, bytes]]) -> bytes:
        """Renderiza um PDF a partir dos arquivos enviados pelo cliente."""
        with TempWorkspace() as ws:
            ws.write_items(items)
            cfg = ws.path / "vivliostyle.config.js"
            if not cfg.exists():
                cfg = generate_config(ws.path)
            return await self._run_and_collect(ws, cfg, label="render_from_items")

    async def render_demo(self) -> bytes:
        """Renderiza um PDF de demonstração gerado internamente."""
        with TempWorkspace() as ws:
            build_demo_project(ws.path)
            cfg = generate_config(ws.path)
            return await self._run_and_collect(ws, cfg, label="render_demo")

    async def _run_and_collect(self, ws: TempWorkspace, cfg: Path, label: str) -> bytes:
        """Executa o Vivliostyle, localiza o PDF gerado e devolve seus bytes.

        Registra os PDFs pré-existentes no workspace antes de chamar o CLI,
        para que o fallback não confunda arquivos enviados pelo cliente com
        o PDF produzido pelo Vivliostyle.
        """
        out = ws.path / "out.pdf"
        existing_pdfs = set(ws.path.rglob("*.pdf"))

        t0 = time.perf_counter()
        await run_cli(ws.path, cfg, out)
        elapsed = time.perf_counter() - t0

        if not out.exists():
            new_pdfs = [p for p in ws.path.rglob("*.pdf") if p not in existing_pdfs]
            if not new_pdfs:
                raise RuntimeError("PDF não gerado")
            out = new_pdfs[0]

        logger.info("%s: vivlio=%.2fs", label, elapsed)
        return out.read_bytes()
