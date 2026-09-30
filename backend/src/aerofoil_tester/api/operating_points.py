"""Reusable named flight conditions, including one confirmed primary screening point."""

from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aerofoil_tester.domain.project_setup import Mission
from aerofoil_tester.storage.project_repository import ProjectRepository


class OperatingPoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = "Primary operating point"
    speed_mps: float | None = None
    altitude_m: float | None = None
    mass_kg: float | None = None
    applicability: str = "2D screening"
    primary: bool = False
    source: str = "derived from mission setup"
    status: Literal["ready", "incomplete"] = "incomplete"
    confirmed: bool = False


class OperatingPointSet(BaseModel):
    points: list[OperatingPoint]


def create_operating_points_router(repository: ProjectRepository) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["operating points"])

    @router.get("/{project_id}/primary-operating-point", response_model=OperatingPoint)
    def get_primary_operating_point(project_id: UUID) -> OperatingPoint:
        point_set = get_operating_points(project_id)
        return next((point for point in point_set.points if point.primary), point_set.points[0])

    @router.put("/{project_id}/primary-operating-point", response_model=OperatingPoint)
    def save_primary_operating_point(project_id: UUID, point: OperatingPoint) -> OperatingPoint:
        existing = get_operating_points(project_id).points
        points = [item.model_copy(update={"primary": item.id == point.id}) for item in existing if item.id != point.id]
        points.append(point.model_copy(update={"primary": True}))
        return next(
            item for item in save_operating_points(project_id, OperatingPointSet(points=points)).points if item.primary
        )

    @router.get("/{project_id}/operating-points", response_model=OperatingPointSet)
    def get_operating_points(project_id: UUID) -> OperatingPointSet:
        mission = repository.mission(project_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        stored = repository.operating_points(project_id)
        points = [OperatingPoint.model_validate(item) for item in stored] if stored else [_from_mission(mission)]
        return OperatingPointSet(points=[_with_status(point) for point in points])

    @router.put("/{project_id}/operating-points", response_model=OperatingPointSet)
    def save_operating_points(project_id: UUID, point_set: OperatingPointSet) -> OperatingPointSet:
        points = [_with_status(point) for point in point_set.points]
        if sum(point.primary for point in points) > 1:
            raise HTTPException(status_code=422, detail="Only one primary operating point may be selected.")
        if not repository.save_operating_points(project_id, [point.model_dump(mode="json") for point in points]):
            raise HTTPException(status_code=404, detail="Project not found.")
        return OperatingPointSet(points=points)

    return router


def _from_mission(mission: Mission) -> OperatingPoint:
    return OperatingPoint(
        speed_mps=mission.cruise_speed_mps,
        altitude_m=mission.altitude_m
        if mission.altitude_m is not None
        else 0.0
        if mission.altitude_mode == "sea_level"
        else None,
        mass_kg=mission.takeoff_mass_kg,
        primary=True,
    )


def _with_status(point: OperatingPoint) -> OperatingPoint:
    status: Literal["ready", "incomplete"] = (
        "ready" if None not in (point.speed_mps, point.altitude_m, point.mass_kg) else "incomplete"
    )
    return point.model_copy(update={"status": status})
