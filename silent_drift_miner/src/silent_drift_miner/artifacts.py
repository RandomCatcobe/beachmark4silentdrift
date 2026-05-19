"""Artifact path handling for the file-based pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .schema import ArtifactType


ARTIFACT_DIRS: dict[ArtifactType, str] = {
    ArtifactType.CANDIDATE: "candidates",
    ArtifactType.TRIAGE: "triage",
    ArtifactType.REPRODUCTION: "reproduction",
    ArtifactType.CURATION: "curation",
    ArtifactType.ORACLE: "oracle",
    ArtifactType.BENCHMARK_PACKAGE: "packages",
    ArtifactType.AUDIT_REPORT: "audit",
}


class ArtifactStore:
    """Resolve every pipeline output underneath one artifact root."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    def dir_for(self, artifact_type: ArtifactType) -> Path:
        return self.resolve(ARTIFACT_DIRS[artifact_type])

    def path_for(self, artifact_type: ArtifactType, name: str | Path) -> Path:
        name_path = Path(name)
        if name_path.is_absolute():
            raise ValueError(f"artifact name must be relative: {name}")
        return self.resolve(ARTIFACT_DIRS[artifact_type], name_path)

    def resolve(self, *parts: str | Path) -> Path:
        path = self.root.joinpath(*parts).resolve()
        return self._ensure_inside(path)

    def resolve_user_path(self, path: str | Path) -> Path:
        user_path = Path(path).expanduser()
        if user_path.is_absolute():
            return self._ensure_inside(user_path.resolve())

        cwd_path = (Path.cwd() / user_path).resolve()
        if self._is_inside(cwd_path):
            return cwd_path
        return self.resolve(user_path)

    def prepare_output_path(self, path: str | Path) -> Path:
        output_path = self._ensure_inside(Path(path).expanduser().resolve())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def write_jsonl(self, artifact_type: ArtifactType, name: str | Path, rows: Iterable[str]) -> Path:
        path = self.prepare_output_path(self.path_for(artifact_type, name))
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.rstrip("\n") + "\n")
        tmp.replace(path)
        return path

    def relative_to_root(self, path: str | Path) -> str:
        return str(self._ensure_inside(Path(path).expanduser().resolve()).relative_to(self.root))

    def _ensure_inside(self, path: Path) -> Path:
        if not self._is_inside(path):
            raise ValueError(f"artifact path escapes root {self.root}: {path}")
        return path

    def _is_inside(self, path: Path) -> bool:
        return path == self.root or path.is_relative_to(self.root)
