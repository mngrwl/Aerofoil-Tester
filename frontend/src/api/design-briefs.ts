/** The API representation used by the first screen. */
export interface DesignBrief {
  id: string;
  origin: 'blank' | 'imported_mesh';
  mesh_filename: string | null;
}

export type DesignPriority = 'high_lift_to_drag';

export interface DesignRequirementsInput {
  passenger_capacity: number;
  route_distance_km: number;
  scheduled_block_time_minutes: number;
  cruise_altitude_m: number;
  priority: DesignPriority;
}

export interface SanityCheck {
  id: string;
  severity: 'error' | 'warning';
  message: string;
}

export interface DesignRequirements extends DesignRequirementsInput {
  derived: {
    schedule_average_speed_kmh: number;
    standard_temperature_celsius: number;
    standard_density_kg_m3: number;
  } | null;
  checks: SanityCheck[];
  finalized_at: string | null;
}

// Keep the browser and API on the same loopback spelling during local development.
const apiBaseUrl = 'http://127.0.0.1:3000';

export interface Project { id: string; name: string; project_type: string; unit_system: string; airfoil: string; created_at: string; }
export interface Mission { aircraft_category: string | null; objective: string | null; speed_mode: string; speed_min_mps: number | null; speed_max_mps: number | null; cruise_speed_mps: number | null; altitude_mode: string; altitude_m: number | null; mass_mode: string; takeoff_mass_kg: number | null; payload_mode: string; payload_mass_kg: number | null; maximum_wingspan_m: number | null; maximum_wing_area_m2: number | null; maximum_takeoff_mass_kg: number | null; minimum_stall_speed_mps: number | null; maximum_root_bending_moment_nm: number | null; }
export interface AnalysisReadiness { available: string[]; missing: string[]; reason: string; }
export interface MissionReview { mission: Mission; readiness: Record<string, AnalysisReadiness>; }
export interface Constraint { id: string; category: string; name: string; operator: '≤' | '≥' | '=' | 'between' | 'outside'; minimum: number | null; maximum: number | null; unit: string | null; scope: string; condition: string | null; constraint_type: 'hard' | 'soft'; source: string; notes: string | null; enabled: boolean; revision: number; status: 'ready' | 'pending' | 'incomplete' | 'conflict'; }
export interface ConstraintSet { constraints: Constraint[]; checks: string[]; }
export interface InitialValue { key: string; label: string; value: number | null; unit: string | null; kind: 'calculated' | 'assumed' | 'user-supplied' | 'optimizer variable'; origin: string; dependencies: string[]; status: 'ready' | 'provisional' | 'missing' | 'conflicting'; accepted: boolean; high_impact: boolean; }
export interface InitialValueSet { values: InitialValue[]; }

async function request(path: string, init?: RequestInit): Promise<DesignBrief> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload ? payload.detail : null;
    throw new Error(typeof detail === 'string' ? detail : 'The design could not be created. Try again.');
  }
  return (await response.json()) as DesignBrief;
}

async function requirementsRequest(
  path: string,
  init?: RequestInit,
): Promise<DesignRequirements> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload ? payload.detail : null;
    if (typeof detail === 'string') {
      throw new Error(detail);
    }
    throw new Error('The Design Brief could not be reviewed. Check the values and try again.');
  }
  return (await response.json()) as DesignRequirements;
}

export function createBlankDesign(): Promise<DesignBrief> {
  return request('/api/design-briefs', { method: 'POST' });
}

export function importMesh(mesh: File): Promise<DesignBrief> {
  const form = new FormData();
  form.append('mesh', mesh);
  return request('/api/design-briefs/import', { method: 'POST', body: form });
}

export function loadDesignRequirements(designId: string): Promise<DesignRequirements> {
  return requirementsRequest(`/api/design-briefs/${designId}/requirements`);
}

export function reviewDesignRequirements(
  designId: string,
  requirements: DesignRequirementsInput,
): Promise<DesignRequirements> {
  return requirementsRequest(`/api/design-briefs/${designId}/requirements/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requirements),
  });
}

export function confirmDesignRequirements(
  designId: string,
  requirements: DesignRequirementsInput,
): Promise<DesignRequirements> {
  return requirementsRequest(`/api/design-briefs/${designId}/requirements`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requirements),
  });
}

async function projectRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) throw new Error('The project could not be saved.');
  return (await response.json()) as T;
}
export function createProject(name: string, projectType: string, unitSystem: string): Promise<Project> { return projectRequest('/api/projects', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: name || null, project_type: projectType, unit_system: unitSystem }) }); }
export function listProjects(): Promise<Project[]> { return projectRequest('/api/projects'); }
export async function deleteProject(projectId: string): Promise<void> { const response = await fetch(`${apiBaseUrl}/api/projects/${projectId}`, { method: 'DELETE' }); if (!response.ok) throw new Error('The project could not be deleted.'); }
export function loadMission(projectId: string): Promise<MissionReview> { return projectRequest(`/api/projects/${projectId}/mission`); }
export function saveMission(projectId: string, mission: Mission): Promise<MissionReview> { return projectRequest(`/api/projects/${projectId}/mission`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(mission) }); }
export function loadConstraints(projectId: string): Promise<ConstraintSet> { return projectRequest(`/api/projects/${projectId}/constraints`); }
export function saveConstraints(projectId: string, constraintSet: ConstraintSet): Promise<ConstraintSet> { return projectRequest(`/api/projects/${projectId}/constraints`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(constraintSet) }); }
export function loadInitialValues(projectId: string): Promise<InitialValueSet> { return projectRequest(`/api/projects/${projectId}/initial-values`); }
export function saveInitialValues(projectId: string, initialValues: InitialValueSet): Promise<InitialValueSet> { return projectRequest(`/api/projects/${projectId}/initial-values`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(initialValues) }); }
