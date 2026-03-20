/**
 * API client for the backend.
 * Handles auth token injection and error handling.
 */

const API_BASE = '/api'

function getToken(): string | null {
  return localStorage.getItem('token')
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
    throw new Error('Sessão expirada')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Erro ${res.status}`)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

// Auth
export const auth = {
  login: (email: string, password: string) =>
    request<import('@/types').TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<import('@/types').User>('/auth/me'),

  changePassword: (current_password: string, new_password: string) =>
    request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password }),
    }),
}

// Análises
export const analises = {
  list: (params?: { area?: string; status?: string; skip?: number; limit?: number }) => {
    const qs = new URLSearchParams()
    if (params?.area) qs.set('area', params.area)
    if (params?.status) qs.set('status', params.status)
    if (params?.skip) qs.set('skip', String(params.skip))
    if (params?.limit) qs.set('limit', String(params.limit))
    return request<import('@/types').AnaliseListItem[]>(`/analises?${qs}`)
  },

  get: (id: number) => request<import('@/types').Analise>(`/analises/${id}`),

  create: (data: Record<string, unknown>) =>
    request<import('@/types').Analise>('/analises', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: Record<string, unknown>) =>
    request<import('@/types').Analise>(`/analises/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request(`/analises/${id}`, { method: 'DELETE' }),
}

// AI
export const ai = {
  extractPdf: async (file: File, model?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (model) formData.append('model', model)

    const token = getToken()
    const res = await fetch(`${API_BASE}/ai/extract-pdf`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || 'Erro na extração')
    }
    return res.json()
  },

  analyze: (data: Record<string, unknown>) =>
    request(`/ai/analyze`, { method: 'POST', body: JSON.stringify(data) }),

  analyzeStream: async function* (data: Record<string, unknown>) {
    const token = getToken()
    const res = await fetch(`${API_BASE}/ai/analyze/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    })

    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      const lines = text.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          yield data
        }
      }
    }
  },

  generateEmail: (data: Record<string, unknown>) =>
    request(`/ai/generate-email`, { method: 'POST', body: JSON.stringify(data) }),

  listPrompts: () => request<Record<string, string[]>>('/ai/prompts'),
}

// Dashboard
export const dashboard = {
  stats: (days = 30) =>
    request<import('@/types').DashboardStats>(`/dashboard/stats?days=${days}`),
}
