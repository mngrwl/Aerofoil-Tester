"""Explicitly confirmed objective for the later candidate search."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aerofoil_tester.storage.project_repository import ProjectRepository


class OptimizationObjective(BaseModel):
    quantity: Literal["lift-to-drag ratio"] = "lift-to-drag ratio"
    direction: Literal["maximize"] = "maximize"
    method: Literal["2D polar screening at selected operating conditions"] = (
        "2D polar screening at selected operating conditions"
    )
    confirmed: bool = False


def create_optimization_router(repository: ProjectRepository) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["optimization"])

    @router.get("/{project_id}/optimization", response_model=OptimizationObjective)
    def get_optimization(project_id: UUID) -> OptimizationObjective:
        if repository.mission(project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        stored = repository.optimization(project_id)
        return OptimizationObjective.model_validate(stored or {})

    @router.put("/{project_id}/optimization", response_model=OptimizationObjective)
    def save_optimization(project_id: UUID, objective: OptimizationObjective) -> OptimizationObjective:
        if not repository.save_optimization(project_id, objective.model_dump()):
            raise HTTPException(status_code=404, detail="Project not found.")
        return objective

    return router
