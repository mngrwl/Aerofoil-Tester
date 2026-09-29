/** The API representation used by the first screen. */
export interface DesignBrief {
  id: string;
  origin: 'blank' | 'imported_mesh';
  mesh_filename: string | null;
}

// Keep the browser and API on the same loopback spelling during local development.
const apiBaseUrl = 'http://127.0.0.1:8000';

async function request(path: string, init?: RequestInit): Promise<DesignBrief> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload ? payload.detail : null;
    throw new Error(typeof detail === 'string' ? detail : 'The design could not be created. Try again.');
  }
  return (await response.json()) as DesignBrief;
}

export function createBlankDesign(): Promise<DesignBrief> {
  return request('/api/design-briefs', { method: 'POST' });
}

export function importMesh(mesh: File): Promise<DesignBrief> {
  const form = new FormData();
  form.append('mesh', mesh);
  return request('/api/design-briefs/import', { method: 'POST', body: form });
}
