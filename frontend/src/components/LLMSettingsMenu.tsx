import { useEffect, useRef, useState } from 'react'
import { Settings2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLLMSettings } from '../hooks/useLLMSettings'
import { useI18n } from '../i18n'
import LLMSettingsPanel from './LLMSettingsPanel'

export default function LLMSettingsMenu() {
  const { user } = useAuth()
  const { settings, setSettings } = useLLMSettings(user?.id)
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  if (!user) return null

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 px-3 py-1.5 text-xs text-gray-300 transition-colors hover:border-gray-700 hover:text-white"
      >
        <Settings2 className="h-3.5 w-3.5" />
        {t('llm.menuLabel')}
        <span
          className={`h-2 w-2 rounded-full ${
            settings.apiKey ? 'bg-emerald-400' : 'bg-gray-600'
          }`}
          aria-hidden="true"
        />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-3 w-[calc(100vw-2rem)] max-w-[40rem]">
          <LLMSettingsPanel settings={settings} onChange={setSettings} />
        </div>
      )}
    </div>
  )
}
