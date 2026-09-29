# Project setup

The setup deliberately avoids wing geometry. NACA 4412 is a reference airfoil section, not a complete wing.

## Stages

1. **Create project** saves a name, project type, units, and the selected NACA 4412 reference.
2. **Aircraft and mission** captures only facts the engineer knows. Every optional quantity is nullable; `null` means unknown, never zero.
3. **Review and readiness** reports the selected reference, known facts, unknown facts, and the missing inputs for each preliminary calculation.

The project can be saved before mass, speed, payload, or altitude are known. Operating cases, geometry, and aerodynamic constraints belong to later workflows.
# Resuming work

The opening screen requests the saved-project list from `GET /api/projects`. Choosing **Continue** requests that selected project's mission with `GET /api/projects/{id}/mission`, then reconstructs the review screen from that stored data. The UUID returned by SQLite remains the canonical project identity for all later saves.

Deleting a project sends `DELETE /api/projects/{id}` only after an explicit confirmation. This permanently removes that project's mission and saved constraint set; it does not affect other projects.

## Mission suggestions

Suggestions are visibly separate from requirements. The current built-in suggestion is the named ISA near-sea-level atmosphere scenario, which a user can apply or replace. Cruise speed and takeoff mass remain unresolved until an approved reference preset or user data is available; aircraft category alone is not a defensible numerical basis. The UI records acceptance of the applied altitude scenario with the mission data.
