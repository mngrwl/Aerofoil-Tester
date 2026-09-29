# pyright: reportAny=false
"""SQLite persistence for the three setup stages."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from aerofoil_tester.domain.project_setup import Mission, Project


class ProjectRepository:
    """Stores project metadata and nullable mission facts without filling gaps."""

    def __init__(self, database_path: Path) -> None:
        self._database_path: Path = database_path

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            _ = connection.execute(
                """CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, project_type TEXT NOT NULL,
                    unit_system TEXT NOT NULL, created_at TEXT NOT NULL, mission_json TEXT NOT NULL
                )"""
            )

    def create(self, name: str | None, project_type: str, unit_system: str) -> Project:
        project_name = name.strip() if name is not None else ""
        project = Project(
            uuid4(), project_name or "Untitled wing project", project_type, unit_system, datetime.now(UTC)
        )
        with self._connection() as connection:
            _ = connection.execute(
                """INSERT INTO projects (id, name, project_type, unit_system, created_at, mission_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(project.id),
                    project.name,
                    project.project_type,
                    project.unit_system,
                    project.created_at.isoformat(),
                    "{}",
                ),
            )
        return project

    def mission(self, project_id: UUID) -> Mission | None:
        with self._connection() as connection:
            row: sqlite3.Row | None = cast(
                sqlite3.Row | None,
                connection.execute("SELECT mission_json FROM projects WHERE id = ?", (str(project_id),)).fetchone(),
            )
        return Mission(**json.loads(cast(str, row["mission_json"]))) if row else None

    def save_mission(self, project_id: UUID, mission: Mission) -> bool:
        payload = json.dumps(
            mission.__dict__
            if hasattr(mission, "__dict__")
            else {field: getattr(mission, field) for field in Mission.__dataclass_fields__}
        )
        with self._connection() as connection:
            cursor = connection.execute("UPDATE projects SET mission_json = ? WHERE id = ?", (payload, str(project_id)))
        return cursor.rowcount == 1

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
