from typing import Iterable, Tuple
import time
import logging

from app.infrastructure.workdir import TempWorkspace
from app.infrastructure.vivlio import generate_config, run_cli, build_demo_project


class RenderService:
    async def render_from_items(self, items: Iterable[Tuple[str, bytes]]) -> bytes:
        logger = logging.getLogger(__name__)
        total_start = time.perf_counter()
        ws = TempWorkspace()
        try:
            prepare_start = time.perf_counter()
            ws.write_items(items)
            cfg = ws.path / "vivliostyle.config.js"
            if not cfg.exists():
                cfg = generate_config(ws.path)
            prepare_end = time.perf_counter()

            out = ws.path / "out.pdf"
            # Registra PDFs pré-existentes para que o fallback não os confunda
            # com PDFs gerados pelo Vivliostyle
            existing_pdfs = set(ws.path.rglob("*.pdf"))
            vivlio_start = time.perf_counter()
            await run_cli(ws.path, cfg, out)
            vivlio_end = time.perf_counter()

            if not out.exists():
                new_pdfs = [p for p in ws.path.rglob("*.pdf") if p not in existing_pdfs]
                if not new_pdfs:
                    raise RuntimeError("PDF not generated")
                out = new_pdfs[0]
            data = out.read_bytes()

            total_end = time.perf_counter()
            prepare_time = prepare_end - prepare_start
            vivlio_time = vivlio_end - vivlio_start
            total_time = total_end - total_start

            logger.info(
                "render_from_items timings: prepare=%.2fs, vivlio=%.2fs, total=%.2fs",
                prepare_time,
                vivlio_time,
                total_time,
            )
            return data
        finally:
            ws.cleanup()

    async def render_demo(self) -> bytes:
        logger = logging.getLogger(__name__)
        total_start = time.perf_counter()
        ws = TempWorkspace()
        try:
            prepare_start = time.perf_counter()
            build_demo_project(ws.path)
            cfg = generate_config(ws.path)
            prepare_end = time.perf_counter()

            out = ws.path / "out.pdf"
            existing_pdfs = set(ws.path.rglob("*.pdf"))
            vivlio_start = time.perf_counter()
            await run_cli(ws.path, cfg, out)
            vivlio_end = time.perf_counter()

            if not out.exists():
                new_pdfs = [p for p in ws.path.rglob("*.pdf") if p not in existing_pdfs]
                if not new_pdfs:
                    raise RuntimeError("PDF not generated")
                out = new_pdfs[0]
            data = out.read_bytes()

            total_end = time.perf_counter()
            prepare_time = prepare_end - prepare_start
            vivlio_time = vivlio_end - vivlio_start
            total_time = total_end - total_start

            logger.info(
                "render_demo timings: prepare=%.2fs, vivlio=%.2fs, total=%.2fs",
                prepare_time,
                vivlio_time,
                total_time,
            )
            return data
        finally:
            ws.cleanup()
