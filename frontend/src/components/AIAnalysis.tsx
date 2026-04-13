import ReactMarkdown from 'react-markdown'
import { Bot } from 'lucide-react'
import { useI18n } from '../i18n'

interface Props {
  summary: string | null
  provider: string | null
  model: string | null
}

export default function AIAnalysis({ summary, provider, model }: Props) {
  const { t } = useI18n()

  if (!summary) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex items-center gap-2 mb-3">
          <Bot className="w-5 h-5 text-gray-500" />
          <h3 className="text-lg font-semibold text-gray-400">{t('ai.emptyTitle')}</h3>
        </div>
        <p className="text-gray-600">{t('ai.emptyBody')}</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-semibold text-white">{t('ai.title')}</h3>
        </div>
        {provider && model && (
          <span className="text-xs text-gray-600 bg-gray-800 px-2 py-1 rounded">
            {provider} / {model}
          </span>
        )}
      </div>
      <div className="markdown-content">
        <ReactMarkdown>{summary}</ReactMarkdown>
      </div>
    </div>
  )
}
