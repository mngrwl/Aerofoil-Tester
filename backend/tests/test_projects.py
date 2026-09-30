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


def test_constraint_set_persists_typed_records_and_reports_readiness(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    project_id = client.post("/api/projects", json={}).json()["id"]
    constraint_set = {
        "constraints": [
            {
                "id": "e4ca54f5-7ca0-4071-b1ef-8969a6e5f19c",
                "name": "Maximum wingspan",
                "category": "integration",
                "operator": "≤",
                "constraint_type": "hard",
                "source": "client / aircraft requirement",
                "scope": "aircraft-wide",
                "condition": None,
                "minimum": None,
                "maximum": 24,
                "unit": "m",
                "enabled": True,
                "revision": 1,
            },
            {
                "id": "1b6c7dfc-3c3a-4e8e-b8c3-f6da04524957",
                "name": "Required lift",
                "category": "performance",
                "operator": "≥",
                "constraint_type": "hard",
                "source": "engineering team limit",
                "scope": "flight condition",
                "condition": "loiter",
                "minimum": 18,
                "maximum": None,
                "unit": "N",
                "enabled": True,
                "revision": 1,
            },
        ],
        "checks": [],
    }
    saved = client.put(f"/api/projects/{project_id}/constraints", json=constraint_set)

    assert saved.status_code == 200
    assert saved.json()["constraints"][0]["status"] == "ready"
    assert saved.json()["constraints"][1]["status"] == "incomplete"
    reloaded = client.get(f"/api/projects/{project_id}/constraints").json()
    assert reloaded["constraints"][0]["id"] == constraint_set["constraints"][0]["id"]
    assert reloaded["constraints"][0]["operator"] == "≤"


def test_saved_projects_can_be_listed_and_resumed(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    first = client.post("/api/projects", json={"name": "Regional wing"}).json()
    second = client.post("/api/projects", json={"name": "Endurance wing"}).json()
    _ = client.put(
        f"/api/projects/{first['id']}/mission",
        json={"objective": "range", "speed_mode": "cruise", "cruise_speed_mps": 52},
    )

    listed = client.get("/api/projects")
    resumed = client.get(f"/api/projects/{first['id']}/mission")

    assert listed.status_code == 200
    assert [project["id"] for project in listed.json()] == [second["id"], first["id"]]
    assert resumed.json()["mission"]["cruise_speed_mps"] == 52


def test_deleting_one_project_does_not_remove_another(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    first = client.post("/api/projects", json={"name": "Delete me"}).json()
    second = client.post("/api/projects", json={"name": "Keep me"}).json()

    deleted = client.delete(f"/api/projects/{first['id']}")

    assert deleted.status_code == 204
    assert client.get(f"/api/projects/{first['id']}/mission").status_code == 404
    assert client.get(f"/api/projects/{second['id']}/mission").status_code == 200


def test_initial_values_calculate_weight_and_keep_assumptions_reviewable(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    project_id = client.post("/api/projects", json={}).json()["id"]
    _ = client.put(
        f"/api/projects/{project_id}/mission",
        json={"mass_mode": "known", "takeoff_mass_kg": 1000, "altitude_mode": "known", "altitude_m": 1000},
    )

    values = client.get(f"/api/projects/{project_id}/initial-values").json()["values"]

    by_key = {value["key"]: value for value in values}
    assert by_key["weight"]["value"] == 9806.65
    assert by_key["air_density"]["status"] == "provisional"
    assert by_key["span"]["kind"] == "optimizer variable"


def test_near_sea_level_scenario_provides_a_provisional_atmosphere(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    project_id = client.post("/api/projects", json={}).json()["id"]
    _ = client.put(f"/api/projects/{project_id}/mission", json={"altitude_mode": "sea_level"})

    values = client.get(f"/api/projects/{project_id}/initial-values").json()["values"]

    density = next(value for value in values if value["key"] == "air_density")
    assert density["value"] == 1.225
    assert density["status"] == "provisional"


def test_dynamic_pressure_does_not_collapse_a_speed_range_to_one_point(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "projects.sqlite3"))
    project_id = client.post("/api/projects", json={}).json()["id"]
    _ = client.put(
        f"/api/projects/{project_id}/mission",
        json={"altitude_mode": "sea_level", "speed_mode": "range", "speed_min_mps": 30, "speed_max_mps": 60},
    )

    values = client.get(f"/api/projects/{project_id}/initial-values").json()["values"]

    dynamic_pressure = next(value for value in values if value["key"] == "dynamic_pressure")
    assert dynamic_pressure["status"] == "missing"
    assert "operating point" in dynamic_pressure["origin"]
