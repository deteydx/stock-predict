import type { LLMProvider, UserLLMSettings } from '../types'
import { DEFAULT_MODELS, MODEL_OPTIONS } from '../hooks/useLLMSettings'
import { useI18n } from '../i18n'

const CUSTOM_MODEL_VALUE = '__custom__'

interface Props {
  settings: UserLLMSettings
  onChange: (settings: UserLLMSettings) => void
}

export default function LLMSettingsPanel({ settings, onChange }: Props) {
  const { t } = useI18n()
  const modelOptions = MODEL_OPTIONS[settings.provider]
  const isCustomModel = !modelOptions.includes(settings.model)

  const handleProviderChange = (provider: LLMProvider) => {
    const nextModel = MODEL_OPTIONS[provider].includes(settings.model)
      ? settings.model
      : DEFAULT_MODELS[provider]

    onChange({
      ...settings,
      provider,
      model: nextModel,
    })
  }

  const handleModelChange = (value: string) => {
    onChange({
      ...settings,
      model: value === CUSTOM_MODEL_VALUE ? '' : value,
    })
  }

  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/85 p-5">
      <div className="flex flex-col gap-1 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">{t('llm.title')}</h2>
          <p className="mt-1 text-sm text-gray-500">{t('llm.subtitle')}</p>
        </div>
        <span className="text-xs text-gray-500">{t('llm.storageHint')}</span>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-gray-500">
            {t('llm.provider')}
          </span>
          <select
            value={settings.provider}
            onChange={(event) => handleProviderChange(event.target.value as LLMProvider)}
            className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-sm text-white outline-none transition-colors focus:border-emerald-500/50"
          >
            <option value="openai">OpenAI</option>
            <option value="claude">Anthropic Claude</option>
          </select>
        </label>

        <div className="space-y-3">
          <label className="block">
            <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-gray-500">
              {t('llm.model')}
            </span>
            <select
              value={isCustomModel ? CUSTOM_MODEL_VALUE : settings.model}
              onChange={(event) => handleModelChange(event.target.value)}
              className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-sm text-white outline-none transition-colors focus:border-emerald-500/50"
            >
              {modelOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
              <option value={CUSTOM_MODEL_VALUE}>{t('llm.customModel')}</option>
            </select>
          </label>

          {isCustomModel && (
            <label className="block">
              <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-gray-500">
                {t('llm.customModelLabel')}
              </span>
              <input
                type="text"
                value={settings.model}
                onChange={(event) =>
                  onChange({
                    ...settings,
                    model: event.target.value,
                  })
                }
                placeholder={t('llm.customModelPlaceholder')}
                className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-gray-600 focus:border-emerald-500/50"
                spellCheck={false}
              />
            </label>
          )}
        </div>

        <label className="block md:col-span-2">
          <span className="mb-2 block text-xs font-medium uppercase tracking-wide text-gray-500">
            {t('llm.apiKey')}
          </span>
          <input
            type="password"
            value={settings.apiKey}
            onChange={(event) =>
              onChange({
                ...settings,
                apiKey: event.target.value,
              })
            }
            placeholder={
              settings.provider === 'openai'
                ? t('llm.apiKeyPlaceholderOpenAI')
                : t('llm.apiKeyPlaceholderClaude')
            }
            className="w-full rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 font-mono text-sm text-white outline-none transition-colors placeholder:text-gray-600 focus:border-emerald-500/50"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
      </div>
    </section>
  )
}
