import { useI18n } from '../i18n'
import type { ResolvedTermExplanation } from '../lib/termExplanations'

interface Props {
  explanation: ResolvedTermExplanation
}

function Section({ label, body }: { label: string; body: string }) {
  return (
    <div className="space-y-1">
      <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-300/80">
        {label}
      </div>
      <p className="text-xs leading-5 text-gray-300">{body}</p>
    </div>
  )
}

export default function MetricExplanationBody({ explanation }: Props) {
  const { t } = useI18n()

  return (
    <div className="space-y-3">
      <Section label={t('explain.calculation')} body={explanation.calculation} />
      <Section label={t('explain.meaning')} body={explanation.meaning} />
      <Section label={t('explain.interpretation')} body={explanation.interpretation} />
      {explanation.current && (
        <Section label={t('explain.current')} body={explanation.current} />
      )}
    </div>
  )
}
