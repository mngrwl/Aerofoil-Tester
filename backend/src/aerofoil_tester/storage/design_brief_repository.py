"""SQLite implementation for storing early design-brief records."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from aerofoil_tester.domain.design_brief import DesignBrief, DesignOrigin


class DesignBriefRepository:
    """Keeps all SQLite details behind a small domain-focused interface."""

    def __init__(self, database_path: Path) -> None:
        self._database_path: Path = database_path

    def initialize(self) -> None:
        """Create the schema if this is the first time the application has run."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            _ = connection.execute(
                """
                CREATE TABLE IF NOT EXISTS design_briefs (
                    id TEXT PRIMARY KEY,
                    origin TEXT NOT NULL CHECK (origin IN ('blank', 'imported_mesh')),
                    created_at TEXT NOT NULL,
                    mesh_filename TEXT,
                    mesh_path TEXT
                )
                """
            )

    def create(
        self, origin: DesignOrigin, mesh_filename: str | None = None, mesh_path: Path | None = None
    ) -> DesignBrief:
        """Save one new design brief and return the same canonical record."""
        design_brief = DesignBrief(
            id=uuid4(),
            origin=origin,
            created_at=datetime.now(UTC),
            mesh_filename=mesh_filename,
            mesh_path=mesh_path,
        )
        with self._connection() as connection:
            _ = connection.execute(
                """
                INSERT INTO design_briefs (id, origin, created_at, mesh_filename, mesh_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(design_brief.id),
                    design_brief.origin.value,
                    design_brief.created_at.isoformat(),
                    design_brief.mesh_filename,
                    str(design_brief.mesh_path) if design_brief.mesh_path else None,
                ),
            )
        return design_brief

    def list_all(self) -> list[DesignBrief]:
        """Return all briefs in creation order for integration checks and future project lists."""
        with self._connection() as connection:
            rows: list[sqlite3.Row] = cast(
                list[sqlite3.Row],
                connection.execute(
                    """
                SELECT id, origin, created_at, mesh_filename, mesh_path
                FROM design_briefs
                ORDER BY created_at ASC
                """
                ).fetchall(),
            )
        return [self._from_row(row) for row in rows]

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DesignBrief:
        return DesignBrief(
            id=UUID(cast(str, row["id"])),
            origin=DesignOrigin(cast(str, row["origin"])),
            created_at=datetime.fromisoformat(cast(str, row["created_at"])),
            mesh_filename=cast(str | None, row["mesh_filename"]),
            mesh_path=Path(cast(str, row["mesh_path"])) if row["mesh_path"] else None,
        )
