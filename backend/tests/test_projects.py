# pyright: reportAny=false
"""Integration coverage for saving an incomplete project setup."""

from pathlib import Path

from fastapi.testclient import TestClient

from aerofoil_tester.main import create_app


def test_project_keeps_unknown_mission_values_as_null(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    created = client.post("/api/projects", json={})

    assert created.status_code == 201
    assert created.json()["name"] == "Untitled wing project"
    project_id = created.json()["id"]
    saved = client.put(
        f"/api/projects/{project_id}/mission",
        json={"aircraft_category": "manned", "objective": "endurance", "speed_mode": "unknown"},
    )

    assert saved.status_code == 200
    assert saved.json()["mission"]["cruise_speed_mps"] is None
    lift_readiness = saved.json()["readiness"]["level-flight lift screening"]
    assert "operating speed" in lift_readiness["missing"]
    assert lift_readiness["reason"] == "Required lift coefficient follows CL = 2W / (rho V² S)."
    assert client.get(f"/api/projects/{project_id}/mission").json() == saved.json()
