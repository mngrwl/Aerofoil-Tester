# Architecture

## Why there are two applications

The browser application is responsible for showing information and collecting a user's choices. The Python application is responsible for validating those choices and storing them. Keeping these responsibilities separate prevents a browser refresh from losing the source of truth.

## Request path

```text
Lit screen → API client → FastAPI route → domain value → SQLite repository
```

The current start screen creates a `DesignBrief`. A design brief will eventually contain the mission, operating envelope, constraints, and geometry choices. At this stage it records only how the design began: blank or imported mesh.

## Storage boundary

Only files in `backend/src/aerofoil_tester/storage/` use SQLite. The rest of the backend works with ordinary Python domain values. This makes database code easy to find and gives the project a future migration path if SQLite stops being sufficient.
