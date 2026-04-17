import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Settings2, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLLMSettings } from '../hooks/useLLMSettings'
import { useIsMobile } from '../hooks/useIsMobile'
import { useI18n } from '../i18n'
import LLMSettingsPanel from './LLMSettingsPanel'

export default function LLMSettingsMenu() {
  const { user } = useAuth()
  const { settings, setSettings } = useLLMSettings(user?.id)
  const { t } = useI18n()
  const isMobile = useIsMobile()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)

    let removePointer: (() => void) | null = null
    if (!isMobile) {
      const handlePointerDown = (event: MouseEvent) => {
        if (!rootRef.current?.contains(event.target as Node)) {
          setOpen(false)
        }
      }
      document.addEventListener('mousedown', handlePointerDown)
      removePointer = () => document.removeEventListener('mousedown', handlePointerDown)
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      removePointer?.()
    }
  }, [open, isMobile])

  useEffect(() => {
    if (!open || !isMobile) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [open, isMobile])

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

      {open && !isMobile && (
        <div className="absolute right-0 top-full z-50 mt-3 w-[calc(100vw-2rem)] max-w-[40rem]">
          <LLMSettingsPanel settings={settings} onChange={setSettings} />
        </div>
      )}

      {open && isMobile && createPortal(
        <div
          className="fixed inset-0 z-[100] flex items-end justify-center bg-black/70"
          onClick={() => setOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
            className="relative max-h-[90vh] w-full overflow-y-auto"
          >
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="close"
              className="absolute right-3 top-3 z-10 rounded-full bg-gray-800/80 p-1.5 text-gray-300 transition-colors hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
            <LLMSettingsPanel settings={settings} onChange={setSettings} />
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
