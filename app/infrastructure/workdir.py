import tempfile
from pathlib import Path
from typing import Iterable, Tuple, List


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


class TempWorkspace:
    """Workspace temporário para montar os arquivos de uma requisição.

    Pode (e deve) ser usado como context manager para garantir que o
    diretório temporário seja sempre removido ao final:

        with TempWorkspace() as ws:
            ws.write_items(items)
            ...
    """

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)

    # --- context manager ------------------------------------------------

    def __enter__(self) -> "TempWorkspace":
        return self

    def __exit__(self, *_) -> None:
        self.cleanup()

    # --- public API -------------------------------------------------------

    def cleanup(self) -> None:
        """Remove o diretório temporário. Chamado automaticamente pelo context manager."""
        self._tmp.cleanup()

    def write_items(self, items: Iterable[Tuple[str, bytes]]) -> List[Path]:
        """Grava cada (caminho_relativo, conteúdo) dentro do workspace.

        Caminhos que tentarem escapar do workspace (path traversal) são
        redirecionados para ``uploaded.bin`` dentro do workspace.
        """
        saved: List[Path] = []
        workspace = self.path.resolve()
        for rel, data in items:
            # Normaliza separadores e constrói o caminho candidato
            norm = rel.strip().replace("\\", "/")
            candidate = (workspace / norm).resolve()
            # Rejeita qualquer caminho que escape o workspace (path traversal)
            try:
                candidate.relative_to(workspace)
                target = candidate
            except ValueError:
                target = workspace / "uploaded.bin"
            _ensure_parent(target)
            target.write_bytes(data)
            saved.append(target)
        return saved
