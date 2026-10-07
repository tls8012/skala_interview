export type Channel = 'info' | 'chat'

export interface Note {
  id: number
  season_key: string
  channel: Channel
  title: string | null
  body: string
  created_at: string
}

export interface NotePage {
  items: Note[]
  next_cursor: string | null
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: 'same-origin',
    cache: 'no-store',
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    let message = '요청을 처리하지 못했습니다.'
    try {
      const result = await response.json()
      if (typeof result.detail === 'string') message = result.detail
    } catch { /* Keep the generic message. */ }
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}

export const api = {
  session: () => request<{ ok: boolean; current_season: string }>('/api/session'),
  login: (password: string) => request<{ ok: boolean; current_season: string }>('/api/session', {
    method: 'POST', body: JSON.stringify({ password }),
  }),
  logout: () => request<{ ok: boolean }>('/api/session', { method: 'DELETE' }),
  seasons: () => request<{ current_season: string; seasons: string[] }>('/api/seasons'),
  notes: (params: { season: string; channel: Channel; q?: string; cursor?: string | null }) => {
    const search = new URLSearchParams({ season: params.season, channel: params.channel, limit: '50' })
    if (params.q) search.set('q', params.q)
    if (params.cursor) search.set('cursor', params.cursor)
    return request<NotePage>(`/api/notes?${search}`)
  },
  note: (id: number) => request<Note>(`/api/notes/${id}`),
  add: (body: { channel: Channel; title: string; body: string; website: string }) =>
    request<{ item: Note | null; quarantined: boolean }>('/api/notes', {
      method: 'POST', body: JSON.stringify(body),
    }),
}
