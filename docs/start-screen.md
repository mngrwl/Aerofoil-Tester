# Start screen

## Purpose

The start screen creates the first durable record for a wing design. It does not yet evaluate aerodynamics or change any design parameters.

## Available paths

- **Start from scratch:** creates a design brief with `origin = blank`.
- **Import a mesh:** accepts an `.stl` or `.obj` file and creates a design brief with `origin = imported_mesh`.

The imported file is copied into the backend data directory. The database records its original name and stored path. A later screen will inspect and parameterize the mesh; importing it does not claim that the mesh is valid for aerodynamic evaluation.
