import { useMemo, useState } from 'react'
import { extractApiErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useI18n } from '../i18n'

type Mode = 'login' | 'register'

function localizeAuthError(code: string | null, t: ReturnType<typeof useI18n>['t']): string {
  if (!code) return t('auth.unexpectedError')
  const mapping: Record<string, string> = {
    invalid_credentials: 'auth.invalidCredentials',
    email_already_registered: 'auth.emailTaken',
    invalid_email: 'auth.invalidEmail',
    password_too_short: 'auth.passwordTooShort',
    authentication_required: 'auth.authenticationRequired',
  }
  return mapping[code] ? t(mapping[code] as never) : code
}

export default function AuthPage() {
  const { login, register } = useAuth()
  const { t } = useI18n()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const title = useMemo(
    () => (mode === 'login' ? t('auth.loginTitle') : t('auth.registerTitle')),
    [mode, t]
  )

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await register(email, password)
      }
    } catch (err) {
      setError(localizeAuthError(extractApiErrorMessage(err), t))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-4 py-12">
      <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900/90 p-8 shadow-2xl shadow-black/20">
        <div className="mb-6">
          <p className="text-xs uppercase tracking-[0.24em] text-emerald-400/80">
            {t('auth.eyebrow')}
          </p>
          <h1 className="mt-3 text-3xl font-bold text-white">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-gray-400">{t('auth.subtitle')}</p>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-2 rounded-xl border border-gray-800 bg-gray-950 p-1">
          {(['login', 'register'] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => {
                setMode(option)
                setError(null)
              }}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                mode === option
                  ? 'bg-emerald-500/15 text-emerald-300'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {option === 'login' ? t('auth.loginTab') : t('auth.registerTab')}
            </button>
          ))}
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-gray-300">
              {t('auth.emailLabel')}
            </span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={t('auth.emailPlaceholder')}
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-white outline-none transition-colors placeholder:text-gray-600 focus:border-emerald-500/50"
              required
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-gray-300">
              {t('auth.passwordLabel')}
            </span>
            <input
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={t('auth.passwordPlaceholder')}
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-white outline-none transition-colors placeholder:text-gray-600 focus:border-emerald-500/50"
              minLength={8}
              required
            />
          </label>

          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting
              ? mode === 'login'
                ? t('auth.loggingIn')
                : t('auth.registering')
              : mode === 'login'
                ? t('auth.loginAction')
                : t('auth.registerAction')}
          </button>
        </form>
      </div>
    </div>
  )
}
