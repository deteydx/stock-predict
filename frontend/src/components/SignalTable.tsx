import { Fragment, useState } from 'react'
import { ChevronDown, ChevronRight, CircleHelp } from 'lucide-react'
import type { HorizonScore, Signal } from '../types'
import { useI18n } from '../i18n'
import { useIsMobile } from '../hooks/useIsMobile'
import MetricExplanationBody from './MetricExplanationBody'
import MetricExplanationDialog from './MetricExplanationDialog'
import { resolveSignalExplanation } from '../lib/termExplanations'

interface Props {
  label: string
  data: HorizonScore | null
}

function scoreBadge(score: number) {
  const colors: Record<number, string> = {
    2: 'bg-emerald-500/20 text-emerald-400',
    1: 'bg-green-500/20 text-green-400',
    0: 'bg-gray-500/20 text-gray-400',
    '-1': 'bg-red-400/20 text-red-400',
    '-2': 'bg-red-500/20 text-red-500',
  }
  const cls = colors[score] || colors[0]
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${cls}`}>
      {score > 0 ? '+' : ''}{score}
    </span>
  )
}

function formatSignalValue(signal: Signal) {
  if (signal.value == null) return '-'
  if (signal.name === 'atr_regime') return `${signal.value.toFixed(2)}x`
  return signal.value.toFixed(2)
}

export default function SignalTable({ label, data }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [expandedSignalName, setExpandedSignalName] = useState<string | null>(null)
  const { language, locale, t, translateSignalName, translateSignalRationale } = useI18n()
  const isMobile = useIsMobile()

  if (!data || data.signals.length === 0) return null

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors"
      >
        <span className="font-medium text-gray-200">{label} {t('signal.tableSuffix')} ({data.signals.length})</span>
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-500" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-3">
          <p className="mb-3 text-xs text-emerald-300/70">{t('explain.hint')}</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs border-b border-gray-800">
                <th className="text-left py-2">{t('signal.column.signal')}</th>
                <th className="text-right py-2">{t('signal.column.value')}</th>
                <th className="text-center py-2">{t('signal.column.score')}</th>
                <th className="text-left py-2 pl-4">{t('signal.column.rationale')}</th>
              </tr>
            </thead>
            <tbody>
              {data.signals.map((signal) => {
                const explanation = resolveSignalExplanation(signal, { language, locale })
                const isOpen = expandedSignalName === signal.name

                return (
                  <Fragment key={signal.name}>
                    <tr className="border-b border-gray-800/50">
                      <td className="py-2 text-gray-300 font-mono text-xs" title={signal.name}>
                        {explanation ? (
                          <button
                            type="button"
                            onClick={() => setExpandedSignalName(isOpen ? null : signal.name)}
                            aria-expanded={isOpen}
                            className="inline-flex items-center gap-1.5 text-left text-gray-300 transition-colors hover:text-emerald-300"
                          >
                            <span>{translateSignalName(signal.name)}</span>
                            <CircleHelp className="h-3.5 w-3.5" />
                          </button>
                        ) : (
                          translateSignalName(signal.name)
                        )}
                      </td>
                      <td className="py-2 text-right text-gray-400 font-mono text-xs">
                        {formatSignalValue(signal)}
                      </td>
                      <td className="py-2 text-center">{scoreBadge(signal.score)}</td>
                      <td className="py-2 pl-4 text-gray-500 text-xs">
                        {translateSignalRationale(signal.name, signal.rationale)}
                      </td>
                    </tr>
                    {explanation && isOpen && !isMobile && (
                      <tr className="border-b border-gray-800/50 bg-gray-950/40">
                        <td colSpan={4} className="pb-3 pt-1">
                          <div className="rounded-lg border border-gray-800 bg-gray-950/80 p-4">
                            <MetricExplanationBody explanation={explanation} />
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {isMobile && (() => {
        const active = data.signals.find((signal) => signal.name === expandedSignalName)
        if (!active) return null
        const explanation = resolveSignalExplanation(active, { language, locale })
        if (!explanation) return null
        return (
          <MetricExplanationDialog
            title={translateSignalName(active.name)}
            explanation={explanation}
            onClose={() => setExpandedSignalName(null)}
          />
        )
      })()}
    </div>
  )
}
