import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { HorizonScore, Signal } from '../types'
import { useI18n } from '../i18n'

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
  const { t, translateSignalName, translateSignalRationale } = useI18n()

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
              {data.signals.map((signal) => (
                <tr key={signal.name} className="border-b border-gray-800/50">
                  <td className="py-2 text-gray-300 font-mono text-xs" title={signal.name}>
                    {translateSignalName(signal.name)}
                  </td>
                  <td className="py-2 text-right text-gray-400 font-mono text-xs">
                    {formatSignalValue(signal)}
                  </td>
                  <td className="py-2 text-center">{scoreBadge(signal.score)}</td>
                  <td className="py-2 pl-4 text-gray-500 text-xs">
                    {translateSignalRationale(signal.name, signal.rationale)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
