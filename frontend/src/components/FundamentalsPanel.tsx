import type { FundamentalsSnapshot } from '../types'
import { useI18n } from '../i18n'

interface Props {
  fundamentals: FundamentalsSnapshot | null
}

export default function FundamentalsPanel({ fundamentals }: Props) {
  const { locale, t } = useI18n()

  if (!fundamentals) return null

  const na = t('score.na')
  const compactCurrency = (value: number | null) => {
    if (value == null) return na
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value)
  }

  const decimal = (value: number | null) => {
    if (value == null) return na
    return value.toFixed(2)
  }

  const percent = (value: number | null) => {
    if (value == null) return na
    return `${(value * 100).toFixed(1)}%`
  }

  const debtToEquity = (value: number | null) => {
    if (value == null) return na
    return value.toFixed(1)
  }

  const items = [
    { label: t('fund.marketCap'), value: compactCurrency(fundamentals.market_cap) },
    { label: t('fund.peTrailing'), value: decimal(fundamentals.pe_trailing) },
    { label: t('fund.peForward'), value: decimal(fundamentals.pe_forward) },
    { label: t('fund.pb'), value: decimal(fundamentals.pb) },
    { label: t('fund.peg'), value: decimal(fundamentals.peg) },
    { label: t('fund.evEbitda'), value: decimal(fundamentals.ev_ebitda) },
    { label: t('fund.roe'), value: percent(fundamentals.roe) },
    { label: t('fund.profitMargin'), value: percent(fundamentals.profit_margin) },
    { label: t('fund.revenueGrowth'), value: percent(fundamentals.revenue_growth) },
    { label: t('fund.earningsGrowth'), value: percent(fundamentals.earnings_growth) },
    { label: t('fund.debtEquity'), value: debtToEquity(fundamentals.debt_to_equity) },
    { label: t('fund.freeCashFlow'), value: compactCurrency(fundamentals.free_cash_flow) },
    { label: t('fund.dividendYield'), value: percent(fundamentals.dividend_yield) },
    { label: t('fund.beta'), value: decimal(fundamentals.beta) },
  ]

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h3 className="text-lg font-semibold text-white">{t('fund.title')}</h3>
          <p className="text-sm text-gray-500 mt-1">{t('fund.subtitle')}</p>
        </div>
        <div className="flex flex-wrap gap-2 justify-end">
          {fundamentals.sector && (
            <span className="text-xs text-sky-300 bg-sky-500/10 border border-sky-500/20 px-2.5 py-1 rounded-full">
              {fundamentals.sector}
            </span>
          )}
          {fundamentals.industry && (
            <span className="text-xs text-gray-300 bg-gray-800 border border-gray-700 px-2.5 py-1 rounded-full">
              {fundamentals.industry}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-lg border border-gray-800 bg-gray-950/70 p-3">
            <div className="text-xs text-gray-500 mb-1">{item.label}</div>
            <div className="text-sm font-mono text-gray-200">{item.value}</div>
          </div>
        ))}
      </div>

      {fundamentals.market_cap == null && fundamentals.pe_trailing == null && fundamentals.revenue_growth == null && (
        <div className="mt-4 text-sm text-gray-500">{t('fund.empty')}</div>
      )}
    </div>
  )
}
