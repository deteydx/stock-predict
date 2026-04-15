import { useEffect, useMemo, useState } from 'react'
import { Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import {
  addToWatchlist,
  deleteAnalysis,
  getRecent,
  getWatchlist,
  removeFromWatchlist,
} from '../api/client'
import type { AnalysisListItem, WatchlistItem } from '../types'
import { useI18n } from '../i18n'
import TickerInput from './TickerInput'

function verdictColor(verdict: string | null): string {
  if (!verdict) return 'text-gray-500'
  if (verdict.includes('Strong Buy')) return 'text-emerald-400'
  if (verdict.includes('Buy')) return 'text-green-400'
  if (verdict.includes('Strong Sell')) return 'text-red-500'
  if (verdict.includes('Sell')) return 'text-red-400'
  return 'text-yellow-400'
}

function sortWatchlist(items: WatchlistItem[]) {
  return [...items].sort((left, right) => left.ticker.localeCompare(right.ticker))
}

export default function HomePage() {
  const navigate = useNavigate()
  const [recent, setRecent] = useState<AnalysisListItem[]>([])
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [watchlistTicker, setWatchlistTicker] = useState('')
  const [addingWatchlist, setAddingWatchlist] = useState(false)
  const [removingTicker, setRemovingTicker] = useState<string | null>(null)
  const [deletingRecentId, setDeletingRecentId] = useState<number | null>(null)
  const { formatDate, formatDateTime, formatVerdict, t } = useI18n()

  useEffect(() => {
    getRecent(100).then(setRecent).catch(() => {})
    getWatchlist().then((items) => setWatchlist(sortWatchlist(items))).catch(() => {})
  }, [])

  const watchlistCount = useMemo(() => watchlist.length, [watchlist])

  const handleAddWatchlist = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const ticker = watchlistTicker.trim().toUpperCase()
    if (!ticker) return

    setAddingWatchlist(true)
    try {
      const item = await addToWatchlist(ticker)
      setWatchlist((current) =>
        sortWatchlist([
          ...current.filter((existing) => existing.ticker !== item.ticker),
          item,
        ])
      )
      setWatchlistTicker('')
    } finally {
      setAddingWatchlist(false)
    }
  }

  const handleDeleteRecent = async (id: number) => {
    if (!window.confirm(t('history.deleteConfirm'))) return
    setDeletingRecentId(id)
    try {
      await deleteAnalysis(id)
      setRecent((current) => current.filter((item) => item.id !== id))
    } finally {
      setDeletingRecentId(null)
    }
  }

  const handleRemoveWatchlist = async (ticker: string) => {
    setRemovingTicker(ticker)
    try {
      await removeFromWatchlist(ticker)
      setWatchlist((current) => current.filter((item) => item.ticker !== ticker))
    } finally {
      setRemovingTicker(null)
    }
  }

  return (
    <div className="flex flex-col items-center pt-12">
      <h1 className="text-4xl font-bold text-white mb-2">{t('home.title')}</h1>
      <p className="text-gray-400 mb-8">{t('home.subtitle')}</p>

      <TickerInput
        onSubmit={(ticker) => navigate(`/analyze/${ticker}`)}
      />

      <div className="mt-12 grid w-full max-w-6xl gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.25fr)]">
        <section className="rounded-2xl border border-gray-800 bg-gray-900/85 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">{t('watchlist.title')}</h2>
              <p className="mt-1 text-sm text-gray-500">
                {t('watchlist.subtitle')}
              </p>
            </div>
            <span className="rounded-full border border-gray-800 bg-gray-950 px-3 py-1 text-xs text-gray-400">
              {t('watchlist.count', { count: watchlistCount })}
            </span>
          </div>

          <form className="mt-4 flex gap-2" onSubmit={handleAddWatchlist}>
            <input
              value={watchlistTicker}
              onChange={(event) => setWatchlistTicker(event.target.value)}
              placeholder={t('watchlist.placeholder')}
              className="flex-1 rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-white outline-none transition-colors placeholder:text-gray-600 focus:border-emerald-500/50"
              maxLength={10}
            />
            <button
              type="submit"
              disabled={addingWatchlist}
              className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {addingWatchlist ? t('watchlist.adding') : t('watchlist.add')}
            </button>
          </form>

          {watchlist.length > 0 ? (
            <div className="mt-4 max-h-[520px] space-y-2 overflow-y-auto pr-1">
              {watchlist.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-gray-800 bg-gray-950/80 px-4 py-3"
                >
                  <button
                    type="button"
                    onClick={() => {
                      const latest = recent.find((r) => r.ticker === item.ticker)
                      navigate(
                        `/analyze/${item.ticker}`,
                        latest ? { state: { analysisId: latest.id } } : undefined
                      )
                    }}
                    className="flex-1 text-left"
                  >
                    <div className="text-sm font-semibold text-white">{item.ticker}</div>
                    <div className="mt-1 text-xs text-gray-500">
                      {item.created_at
                        ? t('watchlist.savedAt', { time: formatDateTime(item.created_at) })
                        : ''}
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleRemoveWatchlist(item.ticker)}
                    title={t('watchlist.remove')}
                    disabled={removingTicker === item.ticker}
                    className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-red-500/10 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-dashed border-gray-800 bg-gray-950/60 px-4 py-6 text-sm text-gray-500">
              {t('watchlist.empty')}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-gray-800 bg-gray-900/85 p-5">
          <h2 className="text-lg font-semibold text-gray-100">{t('home.recent')}</h2>
          <p className="mt-1 text-sm text-gray-500">{t('home.recentSubtitle')}</p>

          {recent.length > 0 ? (
            <div className="mt-4 max-h-[520px] space-y-2 overflow-y-auto pr-1">
              {recent.map((item) => (
                <div
                  key={item.id}
                  className="group flex items-center gap-3 rounded-xl border border-gray-800 bg-gray-950/80 px-4 py-4 transition-colors hover:border-gray-700 hover:bg-gray-900"
                >
                  <button
                    type="button"
                    onClick={() => navigate(`/analyze/${item.ticker}`, { state: { analysisId: item.id } })}
                    className="flex flex-1 items-center justify-between gap-4 text-left"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="text-lg font-bold text-white">{item.ticker}</span>
                        {item.as_of_price != null && (
                          <span className="text-sm text-gray-400">${item.as_of_price.toFixed(2)}</span>
                        )}
                      </div>
                      <div className="mt-2 text-xs text-gray-600">
                        {item.created_at ? formatDate(item.created_at) : ''}
                      </div>
                    </div>
                    <div className="flex flex-wrap justify-end gap-3 text-sm">
                      <span className={verdictColor(item.short_term?.verdict)}>
                        {t('horizon.short.short')}: {formatVerdict(item.short_term?.verdict)}
                      </span>
                      <span className={verdictColor(item.medium_term?.verdict)}>
                        {t('horizon.medium.short')}: {formatVerdict(item.medium_term?.verdict)}
                      </span>
                      <span className={verdictColor(item.long_term?.verdict)}>
                        {t('horizon.long.short')}: {formatVerdict(item.long_term?.verdict)}
                      </span>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDeleteRecent(item.id)}
                    title={t('history.deleteTitle')}
                    disabled={deletingRecentId === item.id}
                    className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-red-500/10 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-dashed border-gray-800 bg-gray-950/60 px-4 py-6 text-sm text-gray-500">
              {t('home.recentEmpty')}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
