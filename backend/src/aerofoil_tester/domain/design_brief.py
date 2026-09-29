"""The smallest durable description of how a user began a design."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID


class DesignOrigin(StrEnum):
    """The two ways a design can enter the application."""

    BLANK = "blank"
    IMPORTED_MESH = "imported_mesh"


@dataclass(frozen=True, slots=True)
class DesignBrief:
    """A persisted design record before mission and aerodynamic data are added."""

    id: UUID
    origin: DesignOrigin
    created_at: datetime
    mesh_filename: str | None = None
    mesh_path: Path | None = None
