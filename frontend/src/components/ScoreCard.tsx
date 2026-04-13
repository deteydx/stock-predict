import type { HorizonScore } from '../types'
import { useI18n } from '../i18n'

interface Props {
  label: string
  data: HorizonScore | null
}

function verdictBg(verdict: string): string {
  if (verdict.includes('Strong Buy')) return 'bg-emerald-500/20 border-emerald-500/50'
  if (verdict.includes('Buy')) return 'bg-green-500/20 border-green-500/50'
  if (verdict.includes('Strong Sell')) return 'bg-red-500/20 border-red-500/50'
  if (verdict.includes('Sell')) return 'bg-red-400/20 border-red-400/50'
  return 'bg-yellow-500/20 border-yellow-500/50'
}

function verdictText(verdict: string): string {
  if (verdict.includes('Strong Buy')) return 'text-emerald-400'
  if (verdict.includes('Buy')) return 'text-green-400'
  if (verdict.includes('Strong Sell')) return 'text-red-500'
  if (verdict.includes('Sell')) return 'text-red-400'
  return 'text-yellow-400'
}

function scoreColor(score: number): string {
  if (score >= 30) return 'bg-emerald-500'
  if (score >= 0) return 'bg-green-500'
  if (score >= -30) return 'bg-yellow-500'
  return 'bg-red-500'
}

export default function ScoreCard({ label, data }: Props) {
  const { formatVerdict, t } = useI18n()

  if (!data) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 flex-1">
        <div className="text-sm text-gray-500 mb-1">{label}</div>
        <div className="text-gray-600">{t('score.na')}</div>
      </div>
    )
  }

  const scorePct = ((data.raw_score + 100) / 200) * 100 // normalize to 0-100%

  return (
    <div className={`rounded-xl border p-5 flex-1 ${verdictBg(data.verdict)}`}>
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold mb-1 ${verdictText(data.verdict)}`}>
        {formatVerdict(data.verdict)}
      </div>
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-xl font-mono text-white">
          {data.raw_score > 0 ? '+' : ''}{data.raw_score.toFixed(0)}
        </span>
        <span className="text-sm text-gray-400">/ 100</span>
      </div>

      {/* Score bar */}
      <div className="bg-gray-700/50 rounded-full h-2 mb-2">
        <div
          className={`h-full rounded-full score-bar ${scoreColor(data.raw_score)}`}
          style={{ width: `${scorePct}%` }}
        />
      </div>

      <div className="flex justify-between text-xs text-gray-500">
        <span>{t('score.confidence')}: {(data.confidence * 100).toFixed(0)}%</span>
        {data.ml_probability_up != null && data.ml_probability_up !== 0.5 && (
          <span>{t('score.mlUp')}: {(data.ml_probability_up * 100).toFixed(0)}% {t('score.up')}</span>
        )}
      </div>
    </div>
  )
}
