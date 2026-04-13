import type { ProgressUpdate } from '../types'
import { useI18n } from '../i18n'

interface Props {
  updates: ProgressUpdate[]
  error: string | null
}

export default function ProgressBar({ updates, error }: Props) {
  const latest = updates[updates.length - 1]
  const progress = latest?.progress ?? 0
  const { t, translateProgress } = useI18n()

  return (
    <div className="w-full max-w-xl mx-auto mt-8">
      <div className="bg-gray-800 rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-emerald-500 transition-all duration-500 ease-out rounded-full"
          style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
        />
      </div>
      <div className="mt-3 text-center">
        {error ? (
          <p className="text-red-400">{error}</p>
        ) : latest ? (
          <p className="text-gray-400">{translateProgress(latest.step, latest.message)}</p>
        ) : (
          <p className="text-gray-500">{t('progress.preparing')}</p>
        )}
      </div>
      <div className="mt-4 space-y-1">
        {updates.map((u, i) => (
          <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
            <span className={u.step === 'error' ? 'text-red-400' : 'text-emerald-400'}>
              {u.progress >= 0 ? `${u.progress}%` : '!!'}
            </span>
            <span>{translateProgress(u.step, u.message)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
