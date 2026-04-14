export type LLMProvider = 'openai' | 'claude'

export interface UserLLMSettings {
  provider: LLMProvider
  model: string
  apiKey: string
}

export interface Signal {
  name: string
  value: number | null
  score: number
  weight: number
  rationale: string
}

export interface LevelSource {
  kind: string
  price: number
  weight: number
  detail: string
}

export interface Level {
  price: number
  kind: 'support' | 'resistance'
  strength: number
  distance_pct: number
  sources: LevelSource[]
}

export interface HorizonScore {
  horizon: string
  raw_score: number
  rule_score: number
  ml_probability_up: number | null
  verdict: string
  confidence: number
  signals: Signal[]
  levels: Level[]
  caveats: string[]
}

export interface NewsItem {
  headline: string
  source: string
  url: string
  published_at: string | null
  sentiment: number
  relevance: number
  summary: string
  category: string
}

export interface FundamentalsSnapshot {
  sector: string | null
  industry: string | null
  market_cap: number | null
  pe_trailing: number | null
  pe_forward: number | null
  pb: number | null
  peg: number | null
  ev_ebitda: number | null
  roe: number | null
  profit_margin: number | null
  revenue_growth: number | null
  earnings_growth: number | null
  debt_to_equity: number | null
  free_cash_flow: number | null
  dividend_yield: number | null
  beta: number | null
}

export interface ChartDataPoint {
  time: string
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
}

export interface Report {
  ticker: string
  company_name: string
  generated_at: string
  as_of_price: number | null
  price_change_pct: number | null
  short_term: HorizonScore | null
  medium_term: HorizonScore | null
  long_term: HorizonScore | null
  news: NewsItem[]
  fundamentals: FundamentalsSnapshot | null
  ai_summary: string | null
  ai_provider: string | null
  ai_model: string | null
  risks: string[]
  caveats: string[]
  data_sources: Record<string, any>
  config_snapshot: Record<string, any>
  chart_data: ChartDataPoint[]
}

export interface AnalysisListItem {
  id: number
  ticker: string
  created_at: string
  as_of_price: number | null
  short_term: { score: number | null; verdict: string | null }
  medium_term: { score: number | null; verdict: string | null }
  long_term: { score: number | null; verdict: string | null }
  ai_summary_preview?: string | null
}

export interface AnalysisDetail {
  id: number
  ticker: string
  created_at: string
  status: string
  as_of_price: number | null
  short_term: { score: number | null; verdict: string | null; confidence: number | null }
  medium_term: { score: number | null; verdict: string | null; confidence: number | null }
  long_term: { score: number | null; verdict: string | null; confidence: number | null }
  ai_summary: string | null
  ai_provider: string | null
  ai_model: string | null
  report: Report | null
}

export interface ProgressUpdate {
  step: string
  progress: number
  message: string
  analysis_id?: number
}

export interface AnalyzeResponse {
  task_id: number | null
  analysis_id: number | null
  cached: boolean
  status: string
}

export interface User {
  id: number
  email: string
  created_at: string | null
}

export interface AuthResponse {
  user: User
}

export interface WatchlistItem {
  id: number
  ticker: string
  created_at: string | null
}
