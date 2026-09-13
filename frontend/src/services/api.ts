export interface ToolSchema {
  name: string
  description: string
  parameters: Record<string, unknown>
}

export interface VoiceConfig {
  system_prompt: string
  greeting: string
  output: { voice: string; format?: { encoding: string } }
  input?: { format?: { encoding: string } }
  tools: ToolSchema[]
}

export interface VoiceTokenResponse {
  token: string
  expires_in_seconds: number
  max_session_duration_seconds: number | null
  config: VoiceConfig
}

export interface Incident {
  id: number
  title: string
  description: string
  device: string
  category: string
  severity: string
  diagnosis: string
  root_cause: string
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export type IncidentFilters = Partial<{
  status: string
  severity: string
  device: string
  q: string
  limit: number
  offset: number
}>

export interface DeviceInfo {
  name: string
  type: string
  ip: string
}

export interface DiagnosisCheck {
  name: string
  status: string
  ok: boolean
  message: string
}

export interface Diagnosis {
  device: string
  ip: string
  status: string
  checks: DiagnosisCheck[]
  nb_issues: number
  severity: string
  root_cause: string
  recommended_actions: string[]
}

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`API ${response.status}: ${detail}`)
  }
  return (await response.json()) as T
}

function toQueryString(filters: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== '') params.append(key, String(value))
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export const api = {
  getVoiceToken: () => request<VoiceTokenResponse>('/voice-token'),

  listIncidents: (filters?: IncidentFilters) =>
    request<PaginatedResponse<Incident>>(`/incidents${toQueryString(filters ?? {})}`),

  listDevices: () => request<DeviceInfo[]>('/diagnostics/devices'),
  getDiagnosis: (device: string) =>
    request<Diagnosis>(
      `/diagnostics/device/${encodeURIComponent(device)}/diagnosis`,
    ),
  runTool: (name: string, args: unknown) =>
    request<unknown>('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ name, arguments: args }),
    }),
}