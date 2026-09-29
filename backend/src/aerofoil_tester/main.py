"""Application factory and local-development configuration."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aerofoil_tester.api.design_briefs import create_router
from aerofoil_tester.storage.design_brief_repository import DesignBriefRepository


def create_app(database_path: Path | None = None, imported_meshes_path: Path | None = None) -> FastAPI:
    """Create an API with paths injectable for tests and fixed locally for normal use."""
    data_path = Path(os.environ.get("AEROFOIL_DATA_PATH", ".data"))
    repository = DesignBriefRepository(database_path or data_path / "aerofoil_tester.sqlite3")
    repository.initialize()

    app = FastAPI(title="Aerofoil Tester API")
    app.add_middleware(
        CORSMiddleware,
        # Both loopback spellings are valid local-development origins.
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_router(repository, imported_meshes_path or data_path / "imported_meshes"))
    return app


app = create_app()
