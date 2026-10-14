import tempfile
from pathlib import Path
from typing import Iterable, Tuple, List


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


class TempWorkspace:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def write_items(self, items: Iterable[Tuple[str, bytes]]) -> List[Path]:
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
            ensure_parent(target)
            target.write_bytes(data)
            saved.append(target)
        return saved
