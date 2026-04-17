import { useState } from 'react'
import { CircleHelp, ChevronDown } from 'lucide-react'
import type { FundamentalsSnapshot } from '../types'
import { useI18n } from '../i18n'
import { useIsMobile } from '../hooks/useIsMobile'
import MetricExplanationBody from './MetricExplanationBody'
import MetricExplanationDialog from './MetricExplanationDialog'
import {
  resolveFundamentalExplanation,
  type FundamentalMetricKey,
} from '../lib/termExplanations'

interface Props {
  fundamentals: FundamentalsSnapshot | null
}

export default function FundamentalsPanel({ fundamentals }: Props) {
  const { language, locale, t } = useI18n()
  const isMobile = useIsMobile()
  const [expandedKey, setExpandedKey] = useState<FundamentalMetricKey | null>(null)

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
    { key: 'market_cap', label: t('fund.marketCap'), rawValue: fundamentals.market_cap, value: compactCurrency(fundamentals.market_cap) },
    { key: 'pe_trailing', label: t('fund.peTrailing'), rawValue: fundamentals.pe_trailing, value: decimal(fundamentals.pe_trailing) },
    { key: 'pe_forward', label: t('fund.peForward'), rawValue: fundamentals.pe_forward, value: decimal(fundamentals.pe_forward) },
    { key: 'pb', label: t('fund.pb'), rawValue: fundamentals.pb, value: decimal(fundamentals.pb) },
    { key: 'peg', label: t('fund.peg'), rawValue: fundamentals.peg, value: decimal(fundamentals.peg) },
    { key: 'ev_ebitda', label: t('fund.evEbitda'), rawValue: fundamentals.ev_ebitda, value: decimal(fundamentals.ev_ebitda) },
    { key: 'roe', label: t('fund.roe'), rawValue: fundamentals.roe, value: percent(fundamentals.roe) },
    { key: 'profit_margin', label: t('fund.profitMargin'), rawValue: fundamentals.profit_margin, value: percent(fundamentals.profit_margin) },
    { key: 'revenue_growth', label: t('fund.revenueGrowth'), rawValue: fundamentals.revenue_growth, value: percent(fundamentals.revenue_growth) },
    { key: 'earnings_growth', label: t('fund.earningsGrowth'), rawValue: fundamentals.earnings_growth, value: percent(fundamentals.earnings_growth) },
    { key: 'debt_to_equity', label: t('fund.debtEquity'), rawValue: fundamentals.debt_to_equity, value: debtToEquity(fundamentals.debt_to_equity) },
    { key: 'free_cash_flow', label: t('fund.freeCashFlow'), rawValue: fundamentals.free_cash_flow, value: compactCurrency(fundamentals.free_cash_flow) },
    { key: 'dividend_yield', label: t('fund.dividendYield'), rawValue: fundamentals.dividend_yield, value: percent(fundamentals.dividend_yield) },
    { key: 'beta', label: t('fund.beta'), rawValue: fundamentals.beta, value: decimal(fundamentals.beta) },
  ] satisfies Array<{
    key: FundamentalMetricKey
    label: string
    rawValue: number | null
    value: string
  }>

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h3 className="text-lg font-semibold text-white">{t('fund.title')}</h3>
          <p className="text-sm text-gray-500 mt-1">{t('fund.subtitle')}</p>
          <p className="text-xs text-emerald-300/70 mt-2">{t('explain.hint')}</p>
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
        {items.map((item) => {
          const explanation = resolveFundamentalExplanation(item.key, item.rawValue, {
            language,
            locale,
          })
          const isOpen = expandedKey === item.key

          return (
            <div key={item.key} className="rounded-lg border border-gray-800 bg-gray-950/70 p-3">
              <button
                type="button"
                onClick={() => setExpandedKey(isOpen ? null : item.key)}
                aria-expanded={isOpen}
                className="w-full text-left"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-xs text-gray-500 mb-1 break-words">{item.label}</div>
                    <div className="text-sm font-mono text-gray-200 break-all">{item.value}</div>
                  </div>
                  <span
                    className="inline-flex shrink-0 items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-1.5 sm:px-2 py-1 text-[11px] text-emerald-300"
                    aria-label={isOpen ? t('explain.hide') : t('explain.show')}
                  >
                    <CircleHelp className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">
                      {isOpen ? t('explain.hide') : t('explain.show')}
                    </span>
                    <ChevronDown className={`h-3.5 w-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                  </span>
                </div>
              </button>

              {explanation && isOpen && !isMobile && (
                <div className="mt-3 border-t border-gray-800 pt-3">
                  <MetricExplanationBody explanation={explanation} />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {fundamentals.market_cap == null && fundamentals.pe_trailing == null && fundamentals.revenue_growth == null && (
        <div className="mt-4 text-sm text-gray-500">{t('fund.empty')}</div>
      )}

      {isMobile && (() => {
        const active = items.find((item) => item.key === expandedKey)
        if (!active) return null
        const explanation = resolveFundamentalExplanation(active.key, active.rawValue, {
          language,
          locale,
        })
        if (!explanation) return null
        return (
          <MetricExplanationDialog
            title={active.label}
            explanation={explanation}
            onClose={() => setExpandedKey(null)}
          />
        )
      })()}
    </div>
  )
}
