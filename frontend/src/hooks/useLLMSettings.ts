import { useEffect, useRef, useState } from 'react'
import { fetchAvailableModels } from '../api/client'
import type { LLMProvider, UserLLMSettings } from '../types'

const STORAGE_KEY_PREFIX = 'stockpredict.llm-settings'

export const DEFAULT_MODELS: Record<LLMProvider, string> = {
  openai: 'gpt-5.4',
  claude: 'claude-sonnet-4-6',
}

// Used only as a fallback when the /api/models call fails or no API key is set yet.
export const FALLBACK_MODEL_OPTIONS: Record<LLMProvider, string[]> = {
  openai: [
    'gpt-5.4',
    'gpt-5.4-mini',
    'gpt-5.4-nano',
    'gpt-4.1',
    'gpt-4.1-mini',
    'gpt-4o',
  ],
  claude: [
    'claude-opus-4-6',
    'claude-sonnet-4-6',
    'claude-haiku-4-5',
    'claude-sonnet-4-20250514',
    'claude-3-7-sonnet-latest',
    'claude-3-5-haiku-latest',
  ],
}

interface AvailableModelsState {
  models: string[]
  recommended: string
  source: 'live' | 'fallback'
  loading: boolean
  error: string | null
}

export function useAvailableModels(provider: LLMProvider, apiKey: string): AvailableModelsState {
  const [state, setState] = useState<AvailableModelsState>(() => ({
    models: FALLBACK_MODEL_OPTIONS[provider],
    recommended: DEFAULT_MODELS[provider],
    source: 'fallback',
    loading: false,
    error: null,
  }))
  const requestIdRef = useRef(0)

  useEffect(() => {
    const trimmedKey = apiKey.trim()
    const requestId = ++requestIdRef.current

    // Reset to fallback immediately when provider changes or key is cleared.
    if (!trimmedKey) {
      setState({
        models: FALLBACK_MODEL_OPTIONS[provider],
        recommended: DEFAULT_MODELS[provider],
        source: 'fallback',
        loading: false,
        error: null,
      })
      return
    }

    setState((prev) => ({ ...prev, loading: true, error: null }))

    const timer = window.setTimeout(async () => {
      try {
        const result = await fetchAvailableModels(provider, trimmedKey)
        if (requestIdRef.current !== requestId) return
        setState({
          models: result.models.length ? result.models : FALLBACK_MODEL_OPTIONS[provider],
          recommended: result.recommended || DEFAULT_MODELS[provider],
          source: result.source,
          loading: false,
          error: null,
        })
      } catch (err) {
        if (requestIdRef.current !== requestId) return
        setState({
          models: FALLBACK_MODEL_OPTIONS[provider],
          recommended: DEFAULT_MODELS[provider],
          source: 'fallback',
          loading: false,
          error: err instanceof Error ? err.message : 'failed_to_load_models',
        })
      }
    }, 500)

    return () => {
      window.clearTimeout(timer)
    }
  }, [provider, apiKey])

  return state
}

function buildStorageKey(userId: number | null | undefined) {
  return `${STORAGE_KEY_PREFIX}:${userId ?? 'default'}`
}

export function getDefaultLLMSettings(provider: LLMProvider = 'openai'): UserLLMSettings {
  return {
    provider,
    model: DEFAULT_MODELS[provider],
    apiKey: '',
  }
}

function sanitizeSettings(value: unknown): UserLLMSettings {
  if (!value || typeof value !== 'object') {
    return getDefaultLLMSettings()
  }

  const candidate = value as Partial<Record<keyof UserLLMSettings, unknown>>
  const provider = candidate.provider === 'claude' ? 'claude' : 'openai'
  const fallbackModel = DEFAULT_MODELS[provider]
  const model =
    typeof candidate.model === 'string' && candidate.model.trim()
      ? candidate.model.trim()
      : fallbackModel
  const apiKey = typeof candidate.apiKey === 'string' ? candidate.apiKey.trim() : ''

  return { provider, model, apiKey }
}

export function getStoredLLMSettings(userId: number | null | undefined): UserLLMSettings {
  if (typeof window === 'undefined' || userId == null) {
    return getDefaultLLMSettings()
  }

  const raw = window.localStorage.getItem(buildStorageKey(userId))
  if (!raw) {
    return getDefaultLLMSettings()
  }

  try {
    return sanitizeSettings(JSON.parse(raw))
  } catch {
    return getDefaultLLMSettings()
  }
}

export function useLLMSettings(userId: number | null | undefined) {
  const [settings, setSettings] = useState<UserLLMSettings>(() => getStoredLLMSettings(userId))
  const [loadedStorageKey, setLoadedStorageKey] = useState<string | null>(
    userId == null ? null : buildStorageKey(userId)
  )

  useEffect(() => {
    if (userId == null) {
      setSettings(getDefaultLLMSettings())
      setLoadedStorageKey(null)
      return
    }

    setSettings(getStoredLLMSettings(userId))
    setLoadedStorageKey(buildStorageKey(userId))
  }, [userId])

  useEffect(() => {
    if (typeof window === 'undefined' || userId == null) return
    const storageKey = buildStorageKey(userId)
    if (loadedStorageKey !== storageKey) return
    window.localStorage.setItem(storageKey, JSON.stringify(settings))
  }, [loadedStorageKey, settings, userId])

  const updateSettings = (nextSettings: UserLLMSettings) => {
    setSettings(nextSettings)
    if (typeof window === 'undefined' || userId == null) return
    const storageKey = buildStorageKey(userId)
    setLoadedStorageKey(storageKey)
    window.localStorage.setItem(storageKey, JSON.stringify(nextSettings))
  }

  return { settings, setSettings: updateSettings }
}
