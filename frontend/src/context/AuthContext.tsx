import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { getCurrentUser, login as loginRequest, logout as logoutRequest, register as registerRequest } from '../api/client'
import type { User } from '../types'

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  status: AuthStatus
  user: User | null
  login: (email: string, password: string) => Promise<User>
  register: (email: string, password: string) => Promise<User>
  logout: () => Promise<void>
  refresh: () => Promise<User | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<User | null>(null)

  const refresh = useCallback(async () => {
    try {
      const response = await getCurrentUser()
      setUser(response.user)
      setStatus('authenticated')
      return response.user
    } catch {
      setUser(null)
      setStatus('unauthenticated')
      return null
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const login = async (email: string, password: string) => {
    const response = await loginRequest(email, password)
    setUser(response.user)
    setStatus('authenticated')
    return response.user
  }

  const register = async (email: string, password: string) => {
    const response = await registerRequest(email, password)
    setUser(response.user)
    setStatus('authenticated')
    return response.user
  }

  const logout = async () => {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
      setStatus('unauthenticated')
    }
  }

  return (
    <AuthContext.Provider value={{ status, user, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
