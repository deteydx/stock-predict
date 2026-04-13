import type { Report } from '../types'
import ScoreCard from './ScoreCard'
import PriceChart from './PriceChart'
import AIAnalysis from './AIAnalysis'
import SignalTable from './SignalTable'
import NewsPanel from './NewsPanel'
import FundamentalsPanel from './FundamentalsPanel'
import { useI18n } from '../i18n'

interface Props {
  report: Report
}

export default function Dashboard({ report }: Props) {
  const { formatDateTime, t, translateCaveat } = useI18n()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-baseline gap-4">
        <h1 className="text-3xl font-bold text-white">{report.ticker}</h1>
        {report.company_name && (
          <span className="text-gray-400">{report.company_name}</span>
        )}
        {report.as_of_price != null && (
          <span className="text-2xl text-white font-mono">
            ${report.as_of_price.toFixed(2)}
          </span>
        )}
        {report.price_change_pct != null && (
          <span
            className={`text-lg font-mono ${
              report.price_change_pct >= 0 ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {report.price_change_pct >= 0 ? '+' : ''}
            {(report.price_change_pct * 100).toFixed(2)}%
          </span>
        )}
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ScoreCard label={t('horizon.short.card')} data={report.short_term} />
        <ScoreCard label={t('horizon.medium.card')} data={report.medium_term} />
        <ScoreCard label={t('horizon.long.card')} data={report.long_term} />
      </div>

      <FundamentalsPanel fundamentals={report.fundamentals} />

      {/* Price Chart */}
      {report.chart_data.length > 0 && (
        <PriceChart data={report.chart_data} />
      )}

      {/* AI Analysis */}
      <AIAnalysis
        summary={report.ai_summary}
        provider={report.ai_provider}
        model={report.ai_model}
      />

      {/* Signals + News side by side */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.35fr)_minmax(26rem,1fr)] 2xl:grid-cols-[minmax(0,1.25fr)_minmax(30rem,1fr)] gap-4">
        <div className="min-w-0 space-y-3">
          <SignalTable label={t('horizon.short.short')} data={report.short_term} />
          <SignalTable label={t('horizon.medium.short')} data={report.medium_term} />
          <SignalTable label={t('horizon.long.short')} data={report.long_term} />
        </div>
        <div className="min-w-0">
          <NewsPanel news={report.news} />
        </div>
      </div>

      {/* Caveats */}
      {report.caveats.length > 0 && (
        <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-yellow-400 mb-2">{t('caveats.title')}</h3>
          <ul className="text-xs text-yellow-300/70 space-y-1">
            {report.caveats.map((c, i) => (
              <li key={i}>- {translateCaveat(c)}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="text-xs text-gray-700 text-center pb-8">
        {t('footer.generatedAt')} {report.generated_at ? formatDateTime(report.generated_at) : t('score.na')}
        {report.data_sources && (
          <span> | {t('footer.bars')}: {JSON.stringify(report.data_sources.bars?.source || t('score.na'))}</span>
        )}
      </div>
    </div>
  )
}
