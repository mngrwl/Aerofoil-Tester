"""HTTP boundary for creating and listing design briefs."""

import shutil
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from aerofoil_tester.domain.design_brief import DesignBrief, DesignOrigin
from aerofoil_tester.storage.design_brief_repository import DesignBriefRepository

SUPPORTED_MESH_EXTENSIONS = {".obj", ".stl"}


class DesignBriefResponse(BaseModel):
    """The subset of a design brief the start screen needs to display."""

    id: str
    origin: DesignOrigin
    mesh_filename: str | None


def create_router(repository: DesignBriefRepository, imported_meshes_path: Path) -> APIRouter:
    """Build routes with explicit dependencies, which keeps tests isolated."""
    router = APIRouter(prefix="/api/design-briefs", tags=["design briefs"])

    @router.post("", response_model=DesignBriefResponse, status_code=status.HTTP_201_CREATED)
    def create_blank_design() -> DesignBriefResponse:
        return _response_from(repository.create(DesignOrigin.BLANK))

    @router.post("/import", response_model=DesignBriefResponse, status_code=status.HTTP_201_CREATED)
    def import_mesh(mesh: Annotated[UploadFile, File()]) -> DesignBriefResponse:
        filename = mesh.filename or "unnamed-mesh"
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_MESH_EXTENSIONS:
            message = "Choose an OBJ or STL mesh file."
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=message)

        imported_meshes_path.mkdir(parents=True, exist_ok=True)
        stored_path = imported_meshes_path / f"{uuid4()}{extension}"
        with stored_path.open("wb") as destination:
            shutil.copyfileobj(mesh.file, destination)

        return _response_from(repository.create(DesignOrigin.IMPORTED_MESH, filename, stored_path))

    @router.get("", response_model=list[DesignBriefResponse])
    def list_design_briefs() -> list[DesignBriefResponse]:
        return [_response_from(design_brief) for design_brief in repository.list_all()]

    return router


def _response_from(design_brief: DesignBrief) -> DesignBriefResponse:
    return DesignBriefResponse(
        id=str(design_brief.id),
        origin=design_brief.origin,
        mesh_filename=design_brief.mesh_filename,
    )
