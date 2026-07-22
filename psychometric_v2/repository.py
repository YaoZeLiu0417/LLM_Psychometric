from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import ResearchProject


class JsonProjectRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, project_id: str) -> Path:
        candidate = Path(project_id)
        if (
            not project_id
            or project_id in {".", ".."}
            or candidate.is_absolute()
            or len(candidate.parts) != 1
            or candidate.name != project_id
        ):
            raise ValueError("project_id must be a single relative path component")

        destination = (self.root / f"{project_id}.json").resolve()
        if destination.parent != self.root:
            raise ValueError("project_id resolves outside the repository root")
        return destination

    def save(self, project: ResearchProject) -> Path:
        destination = self.path_for(project.config.project_id)
        serialized = project.model_dump_json(indent=2)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.root,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(serialized)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, destination)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return destination

    def load(self, project_id: str) -> ResearchProject:
        source = self.path_for(project_id)
        if not source.exists():
            raise FileNotFoundError(f"project not found: {project_id}")
        try:
            return ResearchProject.model_validate_json(
                source.read_text(encoding="utf-8")
            )
        except (UnicodeError, ValidationError) as exc:
            raise ValueError(f"invalid project JSON for {project_id}: {exc}") from exc

    def ensure_seed(
        self, project: ResearchProject | None = None
    ) -> ResearchProject:
        seed = build_demo_project() if project is None else project
        destination = self.path_for(seed.config.project_id)
        if destination.exists():
            return self.load(seed.config.project_id)
        self.save(seed)
        return seed
