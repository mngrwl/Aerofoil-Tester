"""HTTP API for a project brief that permits incomplete engineering knowledge."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from aerofoil_tester.domain.project_setup import AnalysisReadiness, Mission, Project, readiness
from aerofoil_tester.storage.project_repository import ProjectRepository


class ProjectRequest(BaseModel):
    name: str | None = None
    project_type: str = "explore"
    unit_system: str = "si"


class ProjectResponse(ProjectRequest):
    id: UUID
    airfoil: str = "NACA 4412"
    created_at: datetime


class MissionResponse(BaseModel):
    mission: Mission
    readiness: dict[str, AnalysisReadiness]


def create_project_router(repository: ProjectRepository) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["projects"])

    @router.get("", response_model=list[ProjectResponse])
    def list_projects() -> list[ProjectResponse]:
        return [_project_response(project) for project in repository.projects()]

    @router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
    def create_project(request: ProjectRequest) -> ProjectResponse:
        return _project_response(repository.create(request.name, request.project_type, request.unit_system))

    @router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_project(project_id: UUID) -> None:
        if not repository.delete(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    @router.get("/{project_id}/mission", response_model=MissionResponse)
    def get_mission(project_id: UUID) -> MissionResponse:
        mission = repository.mission(project_id)
        if mission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        return MissionResponse(mission=mission, readiness=readiness(mission))

    @router.put("/{project_id}/mission", response_model=MissionResponse)
    def save_mission(project_id: UUID, mission: Mission) -> MissionResponse:
        if not repository.save_mission(project_id, mission):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        return MissionResponse(mission=mission, readiness=readiness(mission))

    return router


def _project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        project_type=project.project_type,
        unit_system=project.unit_system,
        created_at=project.created_at,
    )
