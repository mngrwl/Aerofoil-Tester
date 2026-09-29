"""Project-setup values: unknown facts stay None instead of becoming assumptions."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Project:
    """A project and its selected reference section, before any 3D wing exists."""

    id: UUID
    name: str
    project_type: str
    unit_system: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Mission:
    """Known mission facts; each nullable numeric value means 'not provided', never zero."""

    aircraft_category: str | None = None
    objective: str | None = None
    speed_mode: str = "unknown"
    speed_min_mps: float | None = None
    speed_max_mps: float | None = None
    cruise_speed_mps: float | None = None
    altitude_mode: str = "unknown"
    altitude_m: float | None = None
    mass_mode: str = "unknown"
    takeoff_mass_kg: float | None = None
    payload_mode: str = "unknown"
    payload_mass_kg: float | None = None
    maximum_wingspan_m: float | None = None
    maximum_wing_area_m2: float | None = None
    maximum_takeoff_mass_kg: float | None = None
    minimum_stall_speed_mps: float | None = None
    maximum_root_bending_moment_nm: float | None = None


@dataclass(frozen=True, slots=True)
class AnalysisReadiness:
    """Evidence for one calculation: supplied facts, missing facts, and their purpose."""

    available: tuple[str, ...]
    missing: tuple[str, ...]
    reason: str


def readiness(mission: Mission) -> dict[str, AnalysisReadiness]:
    """Explain what is usable now and why another value is still required."""
    missing_for_lift: list[str] = []
    if mission.takeoff_mass_kg is None:
        missing_for_lift.append("takeoff mass")
    if mission.cruise_speed_mps is None and (mission.speed_min_mps is None or mission.speed_max_mps is None):
        missing_for_lift.append("operating speed")
    if mission.altitude_m is None:
        missing_for_lift.append("altitude or an atmospheric assumption")
    speed_known = mission.cruise_speed_mps is not None or (
        mission.speed_min_mps is not None and mission.speed_max_mps is not None
    )
    lift_available = [
        "takeoff mass" if mission.takeoff_mass_kg is not None else "",
        "operating speed" if speed_known else "",
        "altitude" if mission.altitude_m is not None else "",
    ]
    return {
        "2D airfoil analysis": AnalysisReadiness(
            tuple(value for value in ["operating speed" if speed_known else ""] if value),
            tuple(value for value in ["operating speed" if not speed_known else "", "local chord"] if value),
            "Reynolds number needs air density, speed, and a local chord.",
        ),
        "level-flight lift screening": AnalysisReadiness(
            tuple(value for value in lift_available if value),
            tuple([*missing_for_lift, "wing area"]),
            "Required lift coefficient follows CL = 2W / (rho V² S).",
        ),
        "stall-speed screening": AnalysisReadiness(
            tuple(value for value in ["takeoff mass" if mission.takeoff_mass_kg is not None else ""] if value),
            tuple(
                value
                for value in [
                    "takeoff mass" if mission.takeoff_mass_kg is None else "",
                    "wing area",
                    "validated maximum lift coefficient",
                ]
                if value
            ),
            "Stall speed needs weight, wing area, density, and a validated maximum lift coefficient.",
        ),
    }
