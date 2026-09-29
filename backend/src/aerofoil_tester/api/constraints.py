"""Typed constraint records and honest readiness checks for the wing-design search."""

from typing import Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from aerofoil_tester.domain.project_setup import Mission
from aerofoil_tester.storage.project_repository import ProjectRepository

ConstraintStatus = Literal["ready", "pending", "incomplete", "conflict"]
ConstraintType = Literal["hard", "soft"]
Operator = Literal["≤", "≥", "=", "between", "outside"]


class Constraint(BaseModel):
    """One enforceable rule; status is calculated rather than entered by the engineer."""

    id: UUID = Field(default_factory=uuid4)
    category: str = "geometry"
    name: str
    operator: Operator = "between"
    minimum: float | None = None
    maximum: float | None = None
    unit: str | None = None
    scope: str = "wing-wide"
    condition: str | None = None
    constraint_type: ConstraintType = "hard"
    source: str = "engineering team limit"
    notes: str | None = None
    enabled: bool = True
    revision: int = 1
    status: ConstraintStatus = "incomplete"

    @model_validator(mode="before")
    @classmethod
    def adapt_legacy_record(cls, value: object) -> object:
        """Read first-version records without losing a saved project during the schema upgrade."""
        if not isinstance(value, dict):
            return value
        record = dict(cast(dict[str, object], value))
        _ = record.setdefault("category", record.pop("section", "geometry"))
        _ = record.setdefault("operator", _legacy_operator(record))
        _ = record.setdefault("scope", "wing-wide")
        _ = record.setdefault("condition", record.pop("applicability", None))
        record["constraint_type"] = "soft" if record.get("constraint_type") in {"target", "preference"} else "hard"
        _ = record.setdefault("notes", None)
        _ = record.setdefault("enabled", True)
        _ = record.setdefault("revision", 1)
        return record


class ConstraintSet(BaseModel):
    constraints: list[Constraint]
    checks: list[str]


def create_constraint_router(repository: ProjectRepository) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["constraints"])

    @router.get("/{project_id}/constraints", response_model=ConstraintSet)
    def get_constraints(project_id: UUID) -> ConstraintSet:
        mission = repository.mission(project_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        stored = repository.constraints(project_id) or []
        constraints = [_with_status(Constraint.model_validate(item), mission) for item in stored]
        return ConstraintSet(constraints=constraints, checks=_checks(constraints))

    @router.put("/{project_id}/constraints", response_model=ConstraintSet)
    def save_constraints(project_id: UUID, constraint_set: ConstraintSet) -> ConstraintSet:
        mission = repository.mission(project_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        constraints = [_with_status(constraint, mission) for constraint in constraint_set.constraints]
        payload = [constraint.model_dump(mode="json", exclude={"status"}) for constraint in constraints]
        if not repository.save_constraints(project_id, payload):
            raise HTTPException(status_code=404, detail="Project not found.")
        return ConstraintSet(constraints=constraints, checks=_checks(constraints))

    return router


def _legacy_operator(record: dict[str, object]) -> Operator:
    if record.get("minimum") is not None and record.get("maximum") is not None:
        return "between"
    return "≥" if record.get("minimum") is not None else "≤"


def _with_status(constraint: Constraint, mission: Mission) -> Constraint:
    return constraint.model_copy(update={"status": _status(constraint, mission)})


def _status(constraint: Constraint, mission: Mission) -> ConstraintStatus:
    if not constraint.enabled:
        return "pending"
    if _has_conflict(constraint):
        return "conflict"
    if not constraint.name or not _has_required_values(constraint):
        return "incomplete"
    if constraint.name in {"Required lift", "Stall-speed limit", "L/D target"} and not constraint.condition:
        return "incomplete"
    if constraint.name == "Required lift":
        if mission.takeoff_mass_kg is None or not _speed_known(mission) or mission.altitude_m is None:
            return "incomplete"
        return "pending"
    if constraint.name == "Stall-speed limit":
        return "pending" if mission.takeoff_mass_kg is not None and mission.altitude_m is not None else "incomplete"
    if constraint.name == "Maximum root bending moment":
        return "pending"
    return "ready"


def _has_required_values(constraint: Constraint) -> bool:
    if constraint.operator in {"between", "outside"}:
        return constraint.minimum is not None and constraint.maximum is not None and constraint.unit is not None
    return (constraint.minimum is not None or constraint.maximum is not None) and constraint.unit is not None


def _has_conflict(constraint: Constraint) -> bool:
    return constraint.minimum is not None and constraint.maximum is not None and constraint.minimum > constraint.maximum


def _speed_known(mission: Mission) -> bool:
    return mission.cruise_speed_mps is not None or (
        mission.speed_min_mps is not None and mission.speed_max_mps is not None
    )


def _checks(constraints: list[Constraint]) -> list[str]:
    checks: list[str] = []
    for constraint in constraints:
        if constraint.status == "conflict":
            checks.append(f"{constraint.name}: lower value exceeds upper value.")
        elif constraint.status == "incomplete":
            checks.append(f"{constraint.name}: add its value, unit, or required flight condition before enforcement.")
        elif constraint.status == "pending":
            checks.append(
                f"{constraint.name}: defined, but it requires geometry or analysis results before evaluation."
            )
    return checks
