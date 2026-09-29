# Constraint sets

The constraints screen records the requirements that apply before a wing shape is generated. It is deliberately not a geometry editor or an optimizer.

Each entry uses the same machine-checkable record: library quantity, operator, value or range, dimension-compatible unit, scope, optional flight condition, hard/soft type, source, notes, enabled state, revision, and computed status.

- A **hard limit** rejects a candidate that violates it.
- A **soft limit** records a preference and reports its violation without making a candidate infeasible.

Mission facts remain mission facts; they are not silently transformed into design limits. A blank category is valid: it means the engineer has not stated a bound yet.

The API reports `ready`, `pending`, `incomplete`, or `conflict`, never pass/fail before a real evaluation. It catches inverted ranges and identifies why lift, stall, and root-bending constraints cannot yet be evaluated. Each save also records a constraint revision snapshot for traceability. Later analysis can add physical checks once inputs exist; it must never substitute a guessed engineering limit.

The relevant code is small by design:

- `backend/src/aerofoil_tester/api/constraints.py` defines the typed model, adapts legacy records, and performs checks.
- `backend/src/aerofoil_tester/storage/project_repository.py` stores the chosen constraint list as project data.
- `frontend/src/features/project-setup/project-setup.ts` renders and edits the set.
