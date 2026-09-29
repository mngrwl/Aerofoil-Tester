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
            _ = connection.execute(
                """CREATE TABLE IF NOT EXISTS project_constraints (
                    project_id TEXT PRIMARY KEY, constraints_json TEXT NOT NULL
                )"""
            )
            _ = connection.execute(
                """CREATE TABLE IF NOT EXISTS constraint_revisions (
                    project_id TEXT NOT NULL, constraint_id TEXT NOT NULL, revision INTEGER NOT NULL,
                    saved_at TEXT NOT NULL, constraint_json TEXT NOT NULL,
                    PRIMARY KEY (project_id, constraint_id, revision)
                )"""
            )
            _ = connection.execute(
                """CREATE TABLE IF NOT EXISTS project_initial_values (
                    project_id TEXT PRIMARY KEY, values_json TEXT NOT NULL
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

    def projects(self) -> list[Project]:
        """Return saved projects newest first so a user can resume one."""
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT id, name, project_type, unit_system, created_at
                FROM projects ORDER BY created_at DESC"""
            ).fetchall()
        return [
            Project(
                UUID(cast(str, row["id"])),
                cast(str, row["name"]),
                cast(str, row["project_type"]),
                cast(str, row["unit_system"]),
                datetime.fromisoformat(cast(str, row["created_at"])),
            )
            for row in rows
        ]

    def delete(self, project_id: UUID) -> bool:
        """Remove one project and its dependent constraint set as one database change."""
        with self._connection() as connection:
            _ = connection.execute("DELETE FROM constraint_revisions WHERE project_id = ?", (str(project_id),))
            _ = connection.execute("DELETE FROM project_constraints WHERE project_id = ?", (str(project_id),))
            cursor = connection.execute("DELETE FROM projects WHERE id = ?", (str(project_id),))
        return cursor.rowcount == 1

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

    def constraints(self, project_id: UUID) -> list[dict[str, object]] | None:
        with self._connection() as connection:
            row: sqlite3.Row | None = cast(
                sqlite3.Row | None,
                connection.execute(
                    "SELECT constraints_json FROM project_constraints WHERE project_id = ?", (str(project_id),)
                ).fetchone(),
            )
        return cast(list[dict[str, object]], json.loads(cast(str, row["constraints_json"]))) if row else None

    def initial_values(self, project_id: UUID) -> list[dict[str, object]] | None:
        with self._connection() as connection:
            row: sqlite3.Row | None = cast(
                sqlite3.Row | None,
                connection.execute(
                    "SELECT values_json FROM project_initial_values WHERE project_id = ?", (str(project_id),)
                ).fetchone(),
            )
        return cast(list[dict[str, object]], json.loads(cast(str, row["values_json"]))) if row else None

    def save_initial_values(self, project_id: UUID, values: list[dict[str, object]]) -> bool:
        if self.mission(project_id) is None:
            return False
        with self._connection() as connection:
            _ = connection.execute(
                """INSERT INTO project_initial_values (project_id, values_json) VALUES (?, ?)
                ON CONFLICT(project_id) DO UPDATE SET values_json = excluded.values_json""",
                (str(project_id), json.dumps(values)),
            )
        return True

    def save_constraints(self, project_id: UUID, constraints: list[dict[str, object]]) -> bool:
        if self.mission(project_id) is None:
            return False
        with self._connection() as connection:
            _ = connection.execute(
                """INSERT INTO project_constraints (project_id, constraints_json) VALUES (?, ?)
                ON CONFLICT(project_id) DO UPDATE SET constraints_json = excluded.constraints_json""",
                (str(project_id), json.dumps(constraints)),
            )
            for constraint in constraints:
                _ = connection.execute(
                    """INSERT OR REPLACE INTO constraint_revisions
                    (project_id, constraint_id, revision, saved_at, constraint_json) VALUES (?, ?, ?, ?, ?)""",
                    (
                        str(project_id),
                        str(constraint["id"]),
                        int(cast(int, constraint["revision"])),
                        datetime.now(UTC).isoformat(),
                        json.dumps(constraint),
                    ),
                )
        return True

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
