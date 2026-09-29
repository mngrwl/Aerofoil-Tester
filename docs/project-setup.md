# Project setup

The setup deliberately avoids wing geometry. NACA 4412 is a reference airfoil section, not a complete wing.

## Stages

1. **Create project** saves a name, project type, units, and the selected NACA 4412 reference.
2. **Aircraft and mission** captures only facts the engineer knows. Every optional quantity is nullable; `null` means unknown, never zero.
3. **Review and readiness** reports the selected reference, known facts, unknown facts, and the missing inputs for each preliminary calculation.

The project can be saved before mass, speed, payload, or altitude are known. Operating cases, geometry, and aerodynamic constraints belong to later workflows.
