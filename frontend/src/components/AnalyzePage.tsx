import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useParams, useNavigate } from 'react-router-dom'
import {
  addToWatchlist,
  extractApiErrorMessage,
  getAnalysisDetail,
  getWatchlist,
  removeFromWatchlist,
  startAnalysis,
  subscribeToProgress,
} from '../api/client'
import type { ProgressUpdate, Report } from '../types'
import { useAuth } from '../context/AuthContext'
import { getStoredLLMSettings } from '../hooks/useLLMSettings'
import { useI18n } from '../i18n'
import TickerInput from './TickerInput'
import ProgressBar from './ProgressBar'
import Dashboard from './Dashboard'
import HistoryList from './HistoryList'
import { Download, RefreshCw, Star } from 'lucide-react'

type Phase = 'idle' | 'loading' | 'progress' | 'done' | 'error'

export default function AnalyzePage() {
  const { ticker: paramTicker } = useParams<{ ticker: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const ticker = (paramTicker || '').toUpperCase()
  const [preloadAnalysisId] = useState<number | null>(
    () => (window.history.state?.usr as { analysisId?: number } | null)?.analysisId ?? null
  )
  useEffect(() => {
    if (preloadAnalysisId != null) {
      navigate(location.pathname, { replace: true, state: null })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const { user } = useAuth()
  const { t, language } = useI18n()

  const [phase, setPhase] = useState<Phase>('idle')
  const [updates, setUpdates] = useState<ProgressUpdate[]>([])
  const [report, setReport] = useState<Report | null>(null)
  const [analysisId, setAnalysisId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [savedToWatchlist, setSavedToWatchlist] = useState(false)
  const [watchlistLoading, setWatchlistLoading] = useState(false)
  const progressUnsubscribeRef = useRef<(() => void) | null>(null)
  const requestVersionRef = useRef(0)
  const languageRef = useRef(language)
  useEffect(() => {
    languageRef.current = language
  }, [language])

  const localizeError = (message: string | null) => {
    if (!message) return null
    if (message === 'connection_lost') return t('error.connectionLost')
    if (message === 'load_analysis_failed') return t('error.loadAnalysisFailed')
    if (message === 'analysis_failed') return t('error.analysisFailed')
    return message
  }

  const clearProgressSubscription = useCallback(() => {
    progressUnsubscribeRef.current?.()
    progressUnsubscribeRef.current = null
  }, [])

  const doAnalyze = useCallback(
    async (forceRefresh = false) => {
      if (!ticker) return
      clearProgressSubscription()
      const requestVersion = ++requestVersionRef.current

      setPhase('loading')
      setUpdates([])
      setError(null)
      setReport(null)

      try {
        const resp = await startAnalysis(ticker, forceRefresh, getStoredLLMSettings(user?.id), languageRef.current)
        if (requestVersionRef.current !== requestVersion) return

        if (resp.cached && resp.analysis_id) {
          // Cached result — fetch directly
          setAnalysisId(resp.analysis_id)
          const detail = await getAnalysisDetail(resp.analysis_id)
          if (requestVersionRef.current !== requestVersion) return
          if (detail.report) {
            setReport(detail.report)
          }
          setPhase('done')
          return
        }

        if (resp.task_id) {
          setAnalysisId(resp.task_id)
          setPhase('progress')

          progressUnsubscribeRef.current = subscribeToProgress(
            resp.task_id,
            (update) => {
              if (requestVersionRef.current !== requestVersion) return
              setUpdates((prev) => [...prev, update])
            },
            async () => {
              // Done — fetch the full report
              try {
                const detail = await getAnalysisDetail(resp.task_id!)
                if (requestVersionRef.current !== requestVersion) return
                if (detail.report) {
                  setReport(detail.report)
                }
                progressUnsubscribeRef.current = null
                setPhase('done')
              } catch {
                progressUnsubscribeRef.current = null
                setError('load_analysis_failed')
                setPhase('error')
              }
            },
            (err) => {
              if (requestVersionRef.current !== requestVersion) return
              progressUnsubscribeRef.current = null
              setError(err)
              setPhase('error')
            }
          )
        }
      } catch (err: any) {
        if (requestVersionRef.current !== requestVersion) return
        setError(extractApiErrorMessage(err) || err.message || 'analysis_failed')
        setPhase('error')
      }
    },
    [clearProgressSubscription, ticker, user?.id]
  )

  // Auto-start analysis when page loads (or load a specific historical analysis if provided)
  useEffect(() => {
    if (!ticker) return
    if (preloadAnalysisId) {
      const requestVersion = ++requestVersionRef.current
      clearProgressSubscription()
      setPhase('loading')
      setUpdates([])
      setError(null)
      setReport(null)
      ;(async () => {
        try {
          const detail = await getAnalysisDetail(preloadAnalysisId)
          if (requestVersionRef.current !== requestVersion) return
          setAnalysisId(preloadAnalysisId)
          if (detail.report) setReport(detail.report)
          setPhase('done')
        } catch {
          if (requestVersionRef.current !== requestVersion) return
          setError('load_analysis_failed')
          setPhase('error')
        }
      })()
    } else {
      void doAnalyze(false)
    }
    return () => {
      requestVersionRef.current += 1
      clearProgressSubscription()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clearProgressSubscription, doAnalyze, ticker, preloadAnalysisId])

  useEffect(() => {
    if (!ticker) return
    getWatchlist()
      .then((items) => {
        setSavedToWatchlist(items.some((item) => item.ticker === ticker))
      })
      .catch(() => {})
  }, [ticker])

  const handleToggleWatchlist = async () => {
    if (!ticker) return
    setWatchlistLoading(true)
    try {
      if (savedToWatchlist) {
        await removeFromWatchlist(ticker)
        setSavedToWatchlist(false)
      } else {
        await addToWatchlist(ticker)
        setSavedToWatchlist(true)
      }
    } finally {
      setWatchlistLoading(false)
    }
  }

  const handleExportJSON = () => {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ticker}_analysis.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      {/* Top bar: search + actions */}
      <div className="flex items-center justify-between mb-6 gap-4">
        <TickerInput
          initialValue={ticker}
          onSubmit={(t) => navigate(`/analyze/${t}`)}
        />
        <div className="flex items-center gap-2">
          <button
            onClick={() => void handleToggleWatchlist()}
            disabled={watchlistLoading || !ticker}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
              savedToWatchlist
                ? 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/20'
                : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
            }`}
          >
            <Star className={`w-4 h-4 ${savedToWatchlist ? 'fill-current' : ''}`} />
            {savedToWatchlist ? t('watchlist.removeCurrent') : t('watchlist.saveCurrent')}
          </button>
          {phase === 'done' && (
            <>
              <button
                onClick={() => doAnalyze(true)}
                className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg text-sm transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                {t('action.reanalyze')}
              </button>
              <button
                onClick={handleExportJSON}
                className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-2 rounded-lg text-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                {t('action.exportJson')}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      {phase === 'loading' && (
        <div className="text-center py-16">
          <div className="animate-spin w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-400">{t('analyze.starting', { ticker })}</p>
        </div>
      )}

      {phase === 'progress' && (
        <ProgressBar updates={updates} error={null} />
      )}

      {phase === 'error' && (
        <div className="text-center py-16">
          <ProgressBar updates={updates} error={localizeError(error)} />
          <button
            onClick={() => doAnalyze(true)}
            className="mt-6 bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg transition-colors"
          >
            {t('action.retry')}
          </button>
        </div>
      )}

      {phase === 'done' && report && (
        <div className="space-y-6">
          <div className="min-w-0">
            <HistoryList
              ticker={ticker}
              currentId={analysisId || undefined}
              onSelect={async (id) => {
                setAnalysisId(id)
                const detail = await getAnalysisDetail(id)
                if (detail.report) {
                  setReport(detail.report)
                }
              }}
              onDelete={(id) => {
                if (analysisId === id) {
                  setAnalysisId(null)
                }
              }}
            />
          </div>
          <div className="min-w-0">
            <Dashboard report={report} />
          </div>
        </div>
      )}
    </div>
  )
}
