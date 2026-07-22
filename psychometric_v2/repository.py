from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from pydantic import ValidationError

from psychometric_v2.demo_seed import build_demo_project
from psychometric_v2.models import ResearchProject


_PROJECT_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class JsonProjectRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, project_id: str) -> Path:
        if _PROJECT_ID_PATTERN.fullmatch(project_id) is None:
            raise ValueError(
                "project_id must be a canonical lowercase identifier "
                "containing only alphanumeric segments separated by single hyphens"
            )

        destination = (self.root / f"{project_id}.json").resolve()
        if destination.parent != self.root:
            raise ValueError("project_id resolves outside the repository root")
        return destination

    def _write_temporary(self, destination: Path, serialized: str) -> Path:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(serialized)
                temporary.flush()
                os.fsync(temporary.fileno())
        except BaseException:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        assert temporary_path is not None
        return temporary_path

    def save(self, project: ResearchProject) -> Path:
        destination = self.path_for(project.config.project_id)
        temporary_path = self._write_temporary(
            destination, project.model_dump_json(indent=2)
        )
        try:
            os.replace(temporary_path, destination)
        finally:
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
        temporary_path = self._write_temporary(
            destination, seed.model_dump_json(indent=2)
        )
        try:
            try:
                os.link(temporary_path, destination)
            except FileExistsError:
                return self.load(seed.config.project_id)
            return seed
        finally:
            temporary_path.unlink(missing_ok=True)
