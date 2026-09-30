"""Initial analysis inputs: calculated facts, reviewable assumptions, and optimizer variables."""

from math import pow
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aerofoil_tester.domain.project_setup import Mission
from aerofoil_tester.storage.project_repository import ProjectRepository


class InitialValue(BaseModel):
    key: str
    label: str
    value: float | None = None
    unit: str | None = None
    kind: Literal["calculated", "assumed", "user-supplied", "optimizer variable"]
    origin: str
    dependencies: list[str]
    status: Literal["ready", "provisional", "missing", "conflicting"]
    accepted: bool = False
    high_impact: bool = False


class InitialValueSet(BaseModel):
    values: list[InitialValue]


def create_initial_values_router(repository: ProjectRepository) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["initial values"])

    @router.get("/{project_id}/initial-values", response_model=InitialValueSet)
    def get_initial_values(project_id: UUID) -> InitialValueSet:
        mission = repository.mission(project_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        return InitialValueSet(values=_merge(_derived(mission), repository.initial_values(project_id) or []))

    @router.put("/{project_id}/initial-values", response_model=InitialValueSet)
    def save_initial_values(project_id: UUID, initial_values: InitialValueSet) -> InitialValueSet:
        if not repository.save_initial_values(project_id, [value.model_dump() for value in initial_values.values]):
            raise HTTPException(status_code=404, detail="Project not found.")
        return initial_values

    return router


def _derived(mission: Mission) -> list[InitialValue]:
    atmosphere_altitude = (
        mission.altitude_m if mission.altitude_m is not None else 0.0 if mission.altitude_mode == "sea_level" else None
    )
    density = _isa_density(atmosphere_altitude) if atmosphere_altitude is not None else None
    speed = mission.cruise_speed_mps
    dynamic_pressure_origin = (
        "q = 0.5 * density * speed^2"
        if speed is not None
        else "A single dynamic pressure needs one named operating point; a speed range is an envelope, not a point."
    )
    values = [
        InitialValue(
            key="weight",
            label="Weight",
            value=mission.takeoff_mass_kg * 9.80665 if mission.takeoff_mass_kg else None,
            unit="N",
            kind="calculated",
            origin="W = mg",
            dependencies=["takeoff mass"],
            status="ready" if mission.takeoff_mass_kg is not None else "missing",
        ),
        InitialValue(
            key="air_density",
            label="Atmospheric density",
            value=density,
            unit="kg/m³",
            kind="assumed",
            origin="International Standard Atmosphere (ISA)",
            dependencies=["operating altitude"],
            status="provisional" if density is not None else "missing",
            high_impact=True,
        ),
        InitialValue(
            key="dynamic_pressure",
            label="Dynamic pressure",
            value=0.5 * density * speed**2 if density is not None and speed is not None else None,
            unit="Pa",
            kind="calculated",
            origin=dynamic_pressure_origin,
            dependencies=["air density", "one selected operating-point speed"],
            status="ready" if density is not None and speed is not None else "missing",
        ),
    ]
    values.extend(
        InitialValue(
            key=key,
            label=label,
            kind="optimizer variable",
            origin="Design-space setup",
            dependencies=["engineer-defined bounds"],
            status="missing",
        )
        for key, label in [
            ("span", "Wingspan"),
            ("taper", "Taper ratio"),
            ("sweep", "Sweep"),
            ("twist", "Twist distribution"),
        ]
    )
    return values


def _merge(derived: list[InitialValue], saved: list[dict[str, object]]) -> list[InitialValue]:
    saved_by_key = {str(value["key"]): value for value in saved if "key" in value}
    return [InitialValue.model_validate(saved_by_key.get(value.key, value)) for value in derived]


def _isa_density(altitude_m: float) -> float | None:
    """Tropospheric ISA density only; higher-altitude modelling needs another atmosphere layer."""
    if not 0 <= altitude_m <= 11_000:
        return None
    temperature_ratio = 1 - 0.0065 * altitude_m / 288.15
    return 1.225 * pow(temperature_ratio, 4.25588)
