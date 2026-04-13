import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import type { NewsItem } from '../types'
import { useI18n } from '../i18n'

interface Props {
  news: NewsItem[]
}

function sentimentBadge(sentiment: number) {
  if (sentiment > 0.2) return <span className="text-xs bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">+{sentiment.toFixed(2)}</span>
  if (sentiment < -0.2) return <span className="text-xs bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">{sentiment.toFixed(2)}</span>
  return <span className="text-xs bg-gray-500/20 text-gray-400 px-1.5 py-0.5 rounded">{sentiment.toFixed(2)}</span>
}

function timeAgo(dateStr: string | null, t: (key: any, vars?: Record<string, string | number>) => string): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return t('news.justNow')
  if (hours < 24) return t('news.hoursAgo', { count: hours })
  const days = Math.floor(hours / 24)
  return t('news.daysAgo', { count: days })
}

export default function NewsPanel({ news }: Props) {
  const { formatDateTime, t } = useI18n()
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0)

  if (!news || news.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h3 className="font-semibold text-gray-400 mb-2">{t('news.title')}</h3>
        <p className="text-gray-600 text-sm">{t('news.empty')}</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <h3 className="font-semibold text-gray-300 mb-3">{t('news.title')}</h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {news.slice(0, 15).map((item, i) => (
          <div key={i} className="rounded-lg border border-gray-800/80 bg-gray-950/50">
            <div className="flex items-start gap-2 px-3 py-3">
              <button
                type="button"
                onClick={() => setExpandedIndex((current) => (current === i ? null : i))}
                className="flex-1 min-w-0 text-left"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="text-xs text-gray-500">{item.source}</span>
                      <span
                        className="text-xs text-gray-600"
                        title={item.published_at ? formatDateTime(item.published_at) : undefined}
                      >
                        {timeAgo(item.published_at, t)}
                      </span>
                      {item.category && (
                        <span className="text-[11px] uppercase tracking-wide text-sky-300/70 bg-sky-500/10 px-1.5 py-0.5 rounded">
                          {item.category}
                        </span>
                      )}
                      {sentimentBadge(item.sentiment)}
                    </div>
                    <p className="text-sm leading-6 text-gray-200">{item.headline}</p>
                  </div>
                  <span className="mt-1 flex items-center gap-1 text-xs text-gray-500 flex-shrink-0">
                    {expandedIndex === i ? t('news.collapse') : t('news.expand')}
                    {expandedIndex === i ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </span>
                </div>
              </button>

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-flex items-center gap-1 rounded-md border border-gray-800 px-2 py-1 text-xs text-emerald-400 hover:border-emerald-500/40 hover:text-emerald-300 flex-shrink-0"
                  title={t('news.readOriginal')}
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>

            {expandedIndex === i && (
              <div className="px-3 pb-3 pt-0 border-t border-gray-800/80">
                <div className="pt-3 space-y-3">
                  <div className="text-xs text-gray-500">
                    {t('news.category')}: <span className="text-gray-400">{item.category || '-'}</span>
                  </div>
                  <p className="text-sm leading-6 text-gray-300 whitespace-pre-wrap">
                    {item.summary?.trim() || t('news.summaryMissing')}
                  </p>
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm text-emerald-400 hover:text-emerald-300"
                    >
                      {t('news.readOriginal')}
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
