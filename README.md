# Aerofoil Tester

An educational web application for defining, evaluating, and improving conceptual wing designs.

The project begins with a three-stage setup: project reference, known mission facts, then review/readiness. It then records a constraint set before any wing candidates are generated. Unknown values remain unknown; the app never turns them into silent assumptions.

## Technology

- `frontend/`: Lit web components and TypeScript.
- `backend/`: FastAPI and Python.
- SQLite: local, single-user project storage. The database is created outside source control at `backend/.data/aerofoil_tester.sqlite3`.

## Quick start

Open two terminals from the repository root.

```sh
cd backend
uv sync --all-extras
uv run uvicorn aerofoil_tester.main:app --reload --port 3000
```

```sh
cd frontend
npm install
npm run dev
```

Then open the local address printed by Vite, normally `http://localhost:5173`. The API also accepts
`http://127.0.0.1:5173` as a local development origin.

## Checks

```sh
cd backend && uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest
cd frontend && npm run check
```

## Structure

```text
frontend/src/components/  Reusable visual building blocks
frontend/src/features/    Screen-specific UI and state
frontend/src/api/         Calls to the Python API
backend/src/aerofoil_tester/domain/  Concepts that do not depend on HTTP or the database
backend/src/aerofoil_tester/storage/ SQLite persistence
backend/src/aerofoil_tester/api/     HTTP request handling
docs/                     Explanations for students reading the codebase
```

Read [the project setup](docs/project-setup.md) and [constraint-set](docs/constraints.md) guides before changing the flow.
