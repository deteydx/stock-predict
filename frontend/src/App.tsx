import { LogOut } from 'lucide-react'
import { Route, Routes } from 'react-router-dom'
import AnalyzePage from './components/AnalyzePage'
import AuthPage from './components/AuthPage'
import HomePage from './components/HomePage'
import LLMSettingsMenu from './components/LLMSettingsMenu'
import { useAuth } from './context/AuthContext'
import { useI18n } from './i18n'

export default function App() {
  const { language, setLanguage, t } = useI18n()
  const { status, user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800 px-3 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <div className="flex items-center gap-3 min-w-0">
          <a href="/" className="text-xl font-bold text-white hover:text-emerald-400 transition-colors">
            StockPredict
          </a>
          <span className="hidden md:inline text-sm text-gray-500">{t('app.tagline')}</span>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap justify-end">
          <div className="flex items-center rounded-lg border border-gray-800 bg-gray-900 p-1">
            {(['en', 'zh'] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setLanguage(option)}
                className={`rounded-md px-2 sm:px-3 py-1 text-xs font-medium transition-colors ${
                  language === option
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {option === 'en' ? t('app.lang.en') : t('app.lang.zh')}
              </button>
            ))}
          </div>
          {user && <LLMSettingsMenu />}
          {user && (
            <div className="flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 px-2 sm:px-3 py-1.5 max-w-full">
              <span className="hidden sm:inline text-xs text-gray-400 truncate max-w-[12rem]">{user.email}</span>
              <button
                type="button"
                onClick={() => void logout()}
                aria-label={t('auth.logout')}
                className="inline-flex items-center gap-1 text-xs text-gray-300 transition-colors hover:text-white"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{t('auth.logout')}</span>
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">
        {status === 'loading' ? (
          <div className="flex min-h-[calc(100vh-10rem)] items-center justify-center">
            <p className="text-sm text-gray-400">{t('auth.sessionLoading')}</p>
          </div>
        ) : user ? (
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze/:ticker" element={<AnalyzePage />} />
          </Routes>
        ) : (
          <AuthPage />
        )}
      </main>
    </div>
  )
}
