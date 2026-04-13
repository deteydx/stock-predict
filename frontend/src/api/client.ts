import axios from 'axios'
import type {
  AnalyzeResponse,
  AnalysisDetail,
  AnalysisListItem,
  AuthResponse,
  WatchlistItem,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true,
})

const inflightAnalysisRequests = new Map<string, Promise<AnalyzeResponse>>()

export async function startAnalysis(
  ticker: string,
  forceRefresh = false
): Promise<AnalyzeResponse> {
  const normalizedTicker = ticker.toUpperCase()
  const requestKey = `${normalizedTicker}:${forceRefresh ? 'refresh' : 'default'}`
  const existingRequest = inflightAnalysisRequests.get(requestKey)
  if (existingRequest) {
    return existingRequest
  }

  const request = api.post<AnalyzeResponse>(`/analyze/${normalizedTicker}`, {
    force_refresh: forceRefresh,
  })
    .then(({ data }) => data)
    .finally(() => {
      inflightAnalysisRequests.delete(requestKey)
    })

  inflightAnalysisRequests.set(requestKey, request)
  return request
}

export async function register(
  email: string,
  password: string
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', { email, password })
  return data
}

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { email, password })
  return data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

export async function getCurrentUser(): Promise<AuthResponse> {
  const { data } = await api.get<AuthResponse>('/auth/me')
  return data
}

export async function getAnalysisDetail(id: number): Promise<AnalysisDetail> {
  const { data } = await api.get<AnalysisDetail>(`/analysis/${id}`)
  return data
}

export async function deleteAnalysis(id: number): Promise<void> {
  await api.delete(`/analysis/${id}`)
}

export async function getHistory(
  ticker: string,
  limit = 20
): Promise<AnalysisListItem[]> {
  const { data } = await api.get<AnalysisListItem[]>(`/history/${ticker}`, {
    params: { limit },
  })
  return data
}

export async function getRecent(limit = 20): Promise<AnalysisListItem[]> {
  const { data } = await api.get<AnalysisListItem[]>('/recent', {
    params: { limit },
  })
  return data
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  const { data } = await api.get<WatchlistItem[]>('/watchlist')
  return data
}

export async function addToWatchlist(ticker: string): Promise<WatchlistItem> {
  const { data } = await api.post<WatchlistItem>(`/watchlist/${ticker.toUpperCase()}`)
  return data
}

export async function removeFromWatchlist(ticker: string): Promise<void> {
  await api.delete(`/watchlist/${ticker.toUpperCase()}`)
}

export function subscribeToProgress(
  taskId: number,
  onUpdate: (update: { step: string; progress: number; message: string; analysis_id?: number }) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  const source = new EventSource(`/api/status/${taskId}`)

  source.onmessage = (event) => {
    try {
      const update = JSON.parse(event.data)
      onUpdate(update)
      if (update.step === 'completed' || update.step === 'error') {
        source.close()
        if (update.step === 'completed') {
          onDone()
        } else {
          onError(update.message)
        }
      }
    } catch {
      // ignore parse errors
    }
  }

  source.onerror = () => {
    source.close()
    onError('connection_lost')
  }

  return () => source.close()
}

export function extractApiErrorMessage(error: unknown): string | null {
  if (!axios.isAxiosError(error)) return null
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first?.msg === 'string') {
      const marker = 'Value error, '
      return first.msg.startsWith(marker) ? first.msg.slice(marker.length) : first.msg
    }
  }
  return error.message ?? null
}
