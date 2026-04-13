import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, Trash2 } from 'lucide-react'
import { deleteAnalysis, getHistory } from '../api/client'
import type { AnalysisListItem } from '../types'
import { useI18n } from '../i18n'

interface Props {
  ticker: string
  currentId?: number
  onSelect: (id: number) => void
  onDelete?: (id: number) => void
}

function verdictColor(verdict: string | null): string {
  if (!verdict) return 'text-gray-600'
  if (verdict.includes('Buy')) return 'text-green-400'
  if (verdict.includes('Sell')) return 'text-red-400'
  return 'text-yellow-400'
}

export default function HistoryList({ ticker, currentId, onSelect, onDelete }: Props) {
  const [items, setItems] = useState<AnalysisListItem[]>([])
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [expanded, setExpanded] = useState(false)
  const { formatDateTime, formatVerdict, t } = useI18n()

  const loadHistory = () => {
    getHistory(ticker, 10).then(setItems).catch(() => {})
  }

  useEffect(() => {
    loadHistory()
  }, [ticker])

  const handleDelete = async (id: number) => {
    if (!window.confirm(t('history.deleteConfirm'))) return
    setDeletingId(id)
    try {
      await deleteAnalysis(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
      onDelete?.(id)
    } catch {
      window.alert(t('error.deleteFailed'))
    } finally {
      setDeletingId(null)
    }
  }

  if (items.length === 0) return null

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="w-full flex items-center justify-between gap-3 text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <h3 className="font-semibold text-gray-300">{t('history.title')}</h3>
          <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded-full whitespace-nowrap">
            {t('history.count', { count: items.length })}
          </span>
        </div>
        <span className="inline-flex items-center gap-1 text-xs text-gray-400 whitespace-nowrap">
          {expanded ? t('history.collapse') : t('history.expand')}
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </span>
      </button>

      {expanded && (
        <div className="mt-3 space-y-1 max-h-80 overflow-y-auto pr-1">
          {items.map((item) => (
            <div
              key={item.id}
              className={`flex items-center gap-2 rounded-lg px-2 py-1 text-sm transition-colors ${
                item.id === currentId
                  ? 'bg-emerald-500/10 border border-emerald-500/30'
                  : 'hover:bg-gray-800'
              }`}
            >
              <button
                onClick={() => onSelect(item.id)}
                className="flex-1 min-w-0 flex items-center justify-between gap-4 px-1 py-1 rounded-lg text-left"
              >
                <span className="text-gray-400 text-xs whitespace-nowrap shrink-0">
                  {item.created_at ? formatDateTime(item.created_at) : ''}
                </span>
                <div className="flex gap-3 text-xs whitespace-nowrap shrink-0">
                  <span className={`${verdictColor(item.short_term?.verdict)} whitespace-nowrap`}>
                    S:{formatVerdict(item.short_term?.verdict, true)}
                  </span>
                  <span className={`${verdictColor(item.medium_term?.verdict)} whitespace-nowrap`}>
                    M:{formatVerdict(item.medium_term?.verdict, true)}
                  </span>
                  <span className={`${verdictColor(item.long_term?.verdict)} whitespace-nowrap`}>
                    L:{formatVerdict(item.long_term?.verdict, true)}
                  </span>
                </div>
              </button>
              <button
                type="button"
                onClick={() => void handleDelete(item.id)}
                disabled={deletingId === item.id}
                title={t('history.deleteTitle')}
                className="p-2 rounded-md text-gray-500 hover:text-red-300 hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
