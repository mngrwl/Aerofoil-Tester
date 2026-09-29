# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Integration tests for the first saved design workflow."""

from pathlib import Path

from fastapi.testclient import TestClient

from aerofoil_tester.main import create_app


def test_create_blank_design_persists_to_sqlite(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "designs.sqlite3", tmp_path / "meshes"))

    created = client.post("/api/design-briefs")

    assert created.status_code == 201
    assert created.json()["origin"] == "blank"
    listed = client.get("/api/design-briefs")
    assert listed.json() == [created.json()]


def test_import_obj_mesh_stores_file_and_design_record(tmp_path: Path) -> None:
    meshes_path = tmp_path / "meshes"
    client = TestClient(create_app(tmp_path / "designs.sqlite3", meshes_path))

    created = client.post(
        "/api/design-briefs/import",
        files={"mesh": ("reference-wing.obj", b"v 0 0 0\n", "text/plain")},
    )

    assert created.status_code == 201
    assert created.json()["origin"] == "imported_mesh"
    assert created.json()["mesh_filename"] == "reference-wing.obj"
    assert len(list(meshes_path.glob("*.obj"))) == 1


def test_rejects_unsupported_mesh_type(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path / "designs.sqlite3", tmp_path / "meshes"))

    response = client.post(
        "/api/design-briefs/import",
        files={"mesh": ("reference-wing.txt", b"not a mesh", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Choose an OBJ or STL mesh file."
