import { useEffect, useState, type FormEvent } from 'react'
import { Search } from 'lucide-react'
import { useI18n } from '../i18n'

interface Props {
  onSubmit: (ticker: string) => void
  initialValue?: string
}

export default function TickerInput({ onSubmit, initialValue = '' }: Props) {
  const [value, setValue] = useState(initialValue)
  const { t } = useI18n()

  // Sync when initialValue prop changes (e.g. navigating to a different ticker)
  useEffect(() => {
    setValue(initialValue)
  }, [initialValue])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const ticker = value.trim().toUpperCase()
    if (ticker) {
      onSubmit(ticker)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 w-5 h-5" />
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value.toUpperCase())}
          placeholder={t('ticker.placeholder')}
          className="w-full bg-gray-900 border border-gray-700 rounded-xl pl-12 pr-24 py-4 text-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
          autoFocus
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-5 py-2 rounded-lg transition-colors"
        >
          {t('ticker.submit')}
        </button>
      </div>
    </form>
  )
}
