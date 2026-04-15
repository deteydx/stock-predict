import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

export type Language = 'en' | 'zh'

const STORAGE_KEY = 'stockpredict.language'

const translations = {
  en: {
    'app.tagline': 'Multi-Horizon US Equity Analysis',
    'app.lang.en': 'EN',
    'app.lang.zh': '中文',
    'auth.eyebrow': 'Account Access',
    'auth.loginTitle': 'Sign in to your workspace',
    'auth.registerTitle': 'Create your workspace account',
    'auth.subtitle': 'Use your email and password to keep analyses and watchlists separated for each user.',
    'auth.loginTab': 'Sign In',
    'auth.registerTab': 'Register',
    'auth.emailLabel': 'Email',
    'auth.passwordLabel': 'Password',
    'auth.emailPlaceholder': 'you@example.com',
    'auth.passwordPlaceholder': 'At least 8 characters',
    'auth.showPassword': 'Show password',
    'auth.hidePassword': 'Hide password',
    'auth.loginAction': 'Sign In',
    'auth.registerAction': 'Create Account',
    'auth.loggingIn': 'Signing in...',
    'auth.registering': 'Creating account...',
    'auth.logout': 'Log out',
    'auth.sessionLoading': 'Checking your session...',
    'auth.invalidCredentials': 'Incorrect email or password.',
    'auth.emailTaken': 'This email is already registered.',
    'auth.invalidEmail': 'Please enter a valid email address.',
    'auth.passwordTooShort': 'Password must be at least 8 characters long.',
    'auth.authenticationRequired': 'Please sign in first.',
    'auth.unexpectedError': 'Something went wrong. Please try again.',
    'home.title': 'Stock Analysis',
    'home.subtitle': 'Enter a U.S. stock ticker to get a multi-dimensional AI analysis report.',
    'home.recent': 'Your Recent Analyses',
    'home.recentSubtitle': 'Only your completed analyses appear here.',
    'home.recentEmpty': 'You have not completed any analyses yet.',
    'llm.title': 'LLM Settings',
    'llm.subtitle': 'Each account can use its own API key and model for AI analysis.',
    'llm.menuLabel': 'LLM',
    'llm.storageHint': 'Stored locally in this browser only',
    'llm.provider': 'Provider',
    'llm.model': 'Model',
    'llm.customModel': 'Custom model',
    'llm.customModelLabel': 'Custom model name',
    'llm.customModelPlaceholder': 'Enter the exact model id',
    'llm.apiKey': 'API Key',
    'llm.apiKeyPlaceholderOpenAI': 'Paste your OpenAI API key',
    'llm.apiKeyPlaceholderClaude': 'Paste your Anthropic API key',
    'ticker.placeholder': 'Enter a ticker (e.g. AAPL, TSLA, NVDA)',
    'ticker.submit': 'Analyze',
    'action.reanalyze': 'Reanalyze',
    'action.exportJson': 'Export JSON',
    'action.retry': 'Retry',
    'action.delete': 'Delete',
    'analyze.starting': 'Starting analysis for {ticker}...',
    'error.loadAnalysisFailed': 'Failed to load analysis result',
    'error.analysisFailed': 'Analysis failed',
    'error.connectionLost': 'Connection lost',
    'error.deleteFailed': 'Failed to delete analysis record',
    'history.title': 'History',
    'history.expand': 'Expand',
    'history.collapse': 'Collapse',
    'history.count': '{count} records',
    'history.deleteConfirm': 'Delete this analysis record? This cannot be undone.',
    'history.deleteTitle': 'Delete record',
    'watchlist.title': 'Watchlist',
    'watchlist.subtitle': 'Each account keeps its own list of tickers.',
    'watchlist.count': '{count} tickers',
    'watchlist.placeholder': 'Add ticker to watchlist',
    'watchlist.add': 'Add',
    'watchlist.adding': 'Adding...',
    'watchlist.empty': 'No saved tickers yet.',
    'watchlist.remove': 'Remove from watchlist',
    'watchlist.saveCurrent': 'Save ticker',
    'watchlist.removeCurrent': 'Remove ticker',
    'watchlist.savedAt': 'Saved at {time}',
    'progress.preparing': 'Preparing...',
    'progress.fetching_bars': 'Fetching price history...',
    'progress.fetching_fundamentals': 'Fetching fundamentals...',
    'progress.fetching_news': 'Fetching news...',
    'progress.fetching_macro': 'Fetching macro data...',
    'progress.computing_indicators': 'Computing indicators...',
    'progress.scoring': 'Scoring horizons...',
    'progress.ai_analysis': 'Generating AI analysis...',
    'progress.saving': 'Saving result...',
    'progress.completed': 'Analysis completed',
    'score.na': 'N/A',
    'score.confidence': 'Confidence',
    'score.mlUp': 'ML',
    'score.up': 'up',
    'horizon.short.card': 'Short Term (1-2w)',
    'horizon.medium.card': 'Medium Term (1-6m)',
    'horizon.long.card': 'Long Term (1-3y)',
    'horizon.short.short': 'Short',
    'horizon.medium.short': 'Mid',
    'horizon.long.short': 'Long',
    'signal.tableSuffix': 'Signals',
    'signal.column.signal': 'Signal',
    'signal.column.value': 'Value',
    'signal.column.score': 'Score',
    'signal.column.rationale': 'Rationale',
    'news.title': 'Recent News',
    'news.empty': 'No news available',
    'news.justNow': 'Just now',
    'news.hoursAgo': '{count}h ago',
    'news.daysAgo': '{count}d ago',
    'news.expand': 'Details',
    'news.collapse': 'Hide',
    'news.readOriginal': 'Open source',
    'news.summaryMissing': 'No article summary was returned by the upstream source.',
    'news.category': 'Category',
    'ai.title': 'AI Comprehensive Analysis',
    'ai.emptyTitle': 'AI Analysis',
    'ai.emptyBody': 'AI analysis is not available. Add your API key and model in the browser settings panel.',
    'fund.title': 'Fundamentals',
    'fund.subtitle': 'Raw valuation, profitability, and growth metrics from yfinance.',
    'fund.marketCap': 'Market Cap',
    'fund.peTrailing': 'Trailing P/E',
    'fund.peForward': 'Forward P/E',
    'fund.pb': 'P/B',
    'fund.peg': 'PEG',
    'fund.evEbitda': 'EV/EBITDA',
    'fund.roe': 'ROE',
    'fund.profitMargin': 'Profit Margin',
    'fund.revenueGrowth': 'Revenue Growth',
    'fund.earningsGrowth': 'Earnings Growth',
    'fund.debtEquity': 'Debt / Equity',
    'fund.freeCashFlow': 'Free Cash Flow',
    'fund.dividendYield': 'Dividend Yield',
    'fund.beta': 'Beta',
    'fund.empty': 'Fundamental fields are present but the upstream source did not return key ratios for this ticker.',
    'caveats.title': 'Data Caveats',
    'footer.generatedAt': 'Generated at',
    'footer.bars': 'Bars',
    'caveat.noPriceData': 'No price data available',
    'caveat.noFundamentals': 'Fundamentals data unavailable',
    'caveat.noNewsKey': 'News data unavailable (no Finnhub API key)',
    'caveat.noMacroKey': 'Macro data unavailable (no FRED API key)',
    'caveat.missingSignals': 'Missing signals: {signals}',
    'verdict.strongBuy': 'Strong Buy',
    'verdict.buy': 'Buy',
    'verdict.hold': 'Hold',
    'verdict.sell': 'Sell',
    'verdict.strongSell': 'Strong Sell',
    'verdictShort.strongBuy': 'S.Buy',
    'verdictShort.buy': 'Buy',
    'verdictShort.hold': 'Hold',
    'verdictShort.sell': 'Sell',
    'verdictShort.strongSell': 'S.Sell',
  },
  zh: {
    'app.tagline': '多周期美股分析平台',
    'app.lang.en': 'EN',
    'app.lang.zh': '中文',
    'auth.eyebrow': '账户访问',
    'auth.loginTitle': '登录你的工作区',
    'auth.registerTitle': '创建新的工作区账户',
    'auth.subtitle': '使用邮箱和密码登录，每个用户的分析记录和自选股都会彼此隔离。',
    'auth.loginTab': '登录',
    'auth.registerTab': '注册',
    'auth.emailLabel': '邮箱',
    'auth.passwordLabel': '密码',
    'auth.emailPlaceholder': 'you@example.com',
    'auth.passwordPlaceholder': '至少 8 位字符',
    'auth.showPassword': '显示密码',
    'auth.hidePassword': '隐藏密码',
    'auth.loginAction': '登录',
    'auth.registerAction': '创建账户',
    'auth.loggingIn': '登录中...',
    'auth.registering': '创建中...',
    'auth.logout': '退出',
    'auth.sessionLoading': '正在检查登录状态...',
    'auth.invalidCredentials': '邮箱或密码不正确。',
    'auth.emailTaken': '这个邮箱已经注册过了。',
    'auth.invalidEmail': '请输入有效的邮箱地址。',
    'auth.passwordTooShort': '密码至少需要 8 位字符。',
    'auth.authenticationRequired': '请先登录。',
    'auth.unexpectedError': '发生错误，请稍后重试。',
    'home.title': '股票分析',
    'home.subtitle': '输入美股代码，获取多维度 AI 分析报告。',
    'home.recent': '你的最近分析',
    'home.recentSubtitle': '这里只显示当前账户的已完成分析。',
    'home.recentEmpty': '你还没有完成任何分析。',
    'llm.title': 'LLM 设置',
    'llm.subtitle': '每个账户都可以使用自己的 API Key 和模型来生成 AI 分析。',
    'llm.menuLabel': 'LLM',
    'llm.storageHint': '仅保存在当前浏览器本地',
    'llm.provider': '服务商',
    'llm.model': '模型',
    'llm.customModel': '自定义模型',
    'llm.customModelLabel': '自定义模型名',
    'llm.customModelPlaceholder': '输入完整模型 ID',
    'llm.apiKey': 'API Key',
    'llm.apiKeyPlaceholderOpenAI': '粘贴你的 OpenAI API Key',
    'llm.apiKeyPlaceholderClaude': '粘贴你的 Anthropic API Key',
    'ticker.placeholder': '输入股票代码（如 AAPL、TSLA、NVDA）',
    'ticker.submit': '分析',
    'action.reanalyze': '重新分析',
    'action.exportJson': '导出 JSON',
    'action.retry': '重试',
    'action.delete': '删除',
    'analyze.starting': '正在开始分析 {ticker}...',
    'error.loadAnalysisFailed': '加载分析结果失败',
    'error.analysisFailed': '分析失败',
    'error.connectionLost': '连接中断',
    'error.deleteFailed': '删除分析记录失败',
    'history.title': '历史记录',
    'history.expand': '展开',
    'history.collapse': '收起',
    'history.count': '{count}条记录',
    'history.deleteConfirm': '确认删除这条分析记录吗？删除后无法恢复。',
    'history.deleteTitle': '删除记录',
    'watchlist.title': '自选股',
    'watchlist.subtitle': '每个账户都有独立的股票列表。',
    'watchlist.count': '{count}只股票',
    'watchlist.placeholder': '添加股票代码到自选股',
    'watchlist.add': '添加',
    'watchlist.adding': '添加中...',
    'watchlist.empty': '还没有保存任何股票。',
    'watchlist.remove': '从自选股移除',
    'watchlist.saveCurrent': '加入自选股',
    'watchlist.removeCurrent': '移出自选股',
    'watchlist.savedAt': '保存于 {time}',
    'progress.preparing': '准备中...',
    'progress.fetching_bars': '获取 K 线数据...',
    'progress.fetching_fundamentals': '获取基本面数据...',
    'progress.fetching_news': '获取新闻数据...',
    'progress.fetching_macro': '获取宏观数据...',
    'progress.computing_indicators': '计算指标...',
    'progress.scoring': '评分计算...',
    'progress.ai_analysis': 'AI 分析中...',
    'progress.saving': '保存结果...',
    'progress.completed': '分析完成',
    'score.na': '暂无',
    'score.confidence': '置信度',
    'score.mlUp': '模型',
    'score.up': '上涨',
    'horizon.short.card': '短期（1-2周）',
    'horizon.medium.card': '中期（1-6个月）',
    'horizon.long.card': '长期（1-3年）',
    'horizon.short.short': '短期',
    'horizon.medium.short': '中期',
    'horizon.long.short': '长期',
    'signal.tableSuffix': '信号',
    'signal.column.signal': '信号',
    'signal.column.value': '数值',
    'signal.column.score': '评分',
    'signal.column.rationale': '依据',
    'news.title': '近期新闻',
    'news.empty': '暂无新闻',
    'news.justNow': '刚刚',
    'news.hoursAgo': '{count}小时前',
    'news.daysAgo': '{count}天前',
    'news.expand': '查看详情',
    'news.collapse': '收起',
    'news.readOriginal': '打开原文',
    'news.summaryMissing': '上游新闻源没有返回摘要内容。',
    'news.category': '分类',
    'ai.title': 'AI 综合分析',
    'ai.emptyTitle': 'AI 分析',
    'ai.emptyBody': 'AI 分析不可用。请先在页面里的 LLM 设置中填写 API Key 和模型。',
    'fund.title': '基本面',
    'fund.subtitle': '来自 yfinance 的原始估值、盈利能力和增长指标。',
    'fund.marketCap': '市值',
    'fund.peTrailing': '静态市盈率',
    'fund.peForward': '动态市盈率',
    'fund.pb': '市净率',
    'fund.peg': 'PEG',
    'fund.evEbitda': 'EV/EBITDA',
    'fund.roe': 'ROE',
    'fund.profitMargin': '利润率',
    'fund.revenueGrowth': '营收增长',
    'fund.earningsGrowth': '利润增长',
    'fund.debtEquity': '负债 / 权益',
    'fund.freeCashFlow': '自由现金流',
    'fund.dividendYield': '股息率',
    'fund.beta': 'Beta',
    'fund.empty': '上游数据源返回了基本面对象，但没有提供关键比率字段。',
    'caveats.title': '数据注意事项',
    'footer.generatedAt': '生成时间',
    'footer.bars': '行情来源',
    'caveat.noPriceData': '暂无价格数据',
    'caveat.noFundamentals': '基本面数据不可用',
    'caveat.noNewsKey': '新闻数据不可用（未配置 Finnhub API Key）',
    'caveat.noMacroKey': '宏观数据不可用（未配置 FRED API Key）',
    'caveat.missingSignals': '缺失信号：{signals}',
    'verdict.strongBuy': '强烈买入',
    'verdict.buy': '买入',
    'verdict.hold': '观望',
    'verdict.sell': '卖出',
    'verdict.strongSell': '强烈卖出',
    'verdictShort.strongBuy': '强买',
    'verdictShort.buy': '买入',
    'verdictShort.hold': '观望',
    'verdictShort.sell': '卖出',
    'verdictShort.strongSell': '强卖',
  },
} as const

type TranslationKey = keyof typeof translations.en

interface I18nContextValue {
  language: Language
  setLanguage: (language: Language) => void
  toggleLanguage: () => void
  locale: string
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string
  formatDate: (value: string | number | Date) => string
  formatDateTime: (value: string | number | Date) => string
  formatVerdict: (verdict: string | null | undefined, short?: boolean) => string
  translateProgress: (step: string | undefined, message: string | undefined) => string
  translateCaveat: (caveat: string) => string
  translateSignalName: (name: string) => string
  translateSignalRationale: (name: string, rationale: string) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function detectLanguage(): Language {
  if (typeof window === 'undefined') return 'en'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'en' || stored === 'zh') return stored
  return window.navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template
  return Object.entries(vars).reduce(
    (result, [key, value]) => result.split(`{${key}}`).join(String(value)),
    template
  )
}

function replacePatterns(
  text: string,
  replacers: Array<[RegExp, (...args: string[]) => string]>
) {
  for (const [pattern, formatter] of replacers) {
    const match = text.match(pattern)
    if (match) {
      return formatter(...match.slice(1))
    }
  }
  return text
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(detectLanguage)
  const locale = language === 'zh' ? 'zh-CN' : 'en-US'

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language)
    document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en'
  }, [language])

  const t = (key: TranslationKey, vars?: Record<string, string | number>) =>
    interpolate(translations[language][key] ?? translations.en[key], vars)

  const formatDate = (value: string | number | Date) =>
    new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date(value))

  const formatDateTime = (value: string | number | Date) =>
    new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))

  const formatVerdict = (verdict: string | null | undefined, short = false) => {
    if (!verdict) return t('score.na')
    const keyMap: Record<string, TranslationKey> = short
      ? {
          'Strong Buy': 'verdictShort.strongBuy',
          Buy: 'verdictShort.buy',
          Hold: 'verdictShort.hold',
          Sell: 'verdictShort.sell',
          'Strong Sell': 'verdictShort.strongSell',
        }
      : {
          'Strong Buy': 'verdict.strongBuy',
          Buy: 'verdict.buy',
          Hold: 'verdict.hold',
          Sell: 'verdict.sell',
          'Strong Sell': 'verdict.strongSell',
        }
    const key = keyMap[verdict]
    return key ? t(key) : verdict
  }

  const translateProgress = (step: string | undefined, message: string | undefined) => {
    const keyMap: Record<string, TranslationKey> = {
      fetching_bars: 'progress.fetching_bars',
      fetching_fundamentals: 'progress.fetching_fundamentals',
      fetching_news: 'progress.fetching_news',
      fetching_macro: 'progress.fetching_macro',
      computing_indicators: 'progress.computing_indicators',
      scoring: 'progress.scoring',
      ai_analysis: 'progress.ai_analysis',
      saving: 'progress.saving',
      completed: 'progress.completed',
    }
    const key = step ? keyMap[step] : undefined
    if (key) return t(key)
    return message ?? ''
  }

  const translateCaveat = (caveat: string) => {
    const exactMap: Record<string, TranslationKey> = {
      'No price data available': 'caveat.noPriceData',
      'Fundamentals data unavailable': 'caveat.noFundamentals',
      'News data unavailable (no Finnhub API key)': 'caveat.noNewsKey',
      'Macro data unavailable (no FRED API key)': 'caveat.noMacroKey',
    }
    if (caveat in exactMap) {
      return t(exactMap[caveat])
    }
    if (caveat.startsWith('Missing signals: ')) {
      return t('caveat.missingSignals', {
        signals: caveat.replace('Missing signals: ', ''),
      })
    }
    return caveat
  }

  const translateSignalName = (name: string) => {
    const labels: Record<string, { en: string; zh: string }> = {
      ma_cross: { en: 'MA5 / MA20 Cross', zh: 'MA5 / MA20 交叉' },
      rsi: { en: 'RSI', zh: 'RSI' },
      macd: { en: 'MACD Histogram', zh: 'MACD 柱状图' },
      bollinger: { en: 'Bollinger %B', zh: '布林带 %B' },
      atr_regime: { en: 'ATR Regime', zh: 'ATR 波动状态' },
      obv_trend: { en: 'OBV Trend', zh: 'OBV 趋势' },
      volume_spike: { en: 'Volume Spike', zh: '成交量放大' },
      momentum_5d: { en: '5-Day Momentum', zh: '5日动量' },
      news_sentiment_24h: { en: '24h News Sentiment', zh: '24小时新闻情绪' },
      news_volume_zscore: { en: 'News Volume Z-Score', zh: '新闻数量 Z-Score' },
      ma50_ma200: { en: 'MA50 / MA200 Cross', zh: 'MA50 / MA200 交叉' },
      price_vs_ma200: { en: 'Price vs MA200', zh: '价格相对 MA200' },
      week52_position: { en: '52-Week Position', zh: '52周位置' },
      relative_strength_spy_3m: { en: 'Relative Strength vs SPY (3M)', zh: '相对 SPY 强弱（3个月）' },
      relative_strength_spy_6m: { en: 'Relative Strength vs SPY (6M)', zh: '相对 SPY 强弱（6个月）' },
      eps_growth_trend: { en: 'Earnings Growth', zh: '利润增长' },
      revenue_growth: { en: 'Revenue Growth', zh: '营收增长' },
      volatility_regime: { en: 'Volatility Regime', zh: '波动率状态' },
      pe_percentile: { en: 'Trailing P/E', zh: '静态市盈率' },
      pb_percentile: { en: 'P/B', zh: '市净率' },
      peg: { en: 'PEG', zh: 'PEG' },
      ev_ebitda: { en: 'EV/EBITDA', zh: 'EV/EBITDA' },
      revenue_growth_qoq: { en: 'Revenue Growth (QoQ)', zh: '营收增长 (季度)' },
      earnings_growth_qoq: { en: 'Earnings Growth (QoQ)', zh: '利润增长 (季度)' },
      roe_trend: { en: 'ROE', zh: 'ROE' },
      profitability_margin: { en: 'Profitability Margin', zh: '盈利能力' },
      debt_equity_trend: { en: 'Debt / Equity', zh: '债务 / 权益' },
      yield_curve: { en: 'Yield Curve', zh: '收益率曲线' },
      fed_cycle: { en: 'Fed Cycle', zh: '联储周期' },
      cpi_trend: { en: 'CPI Trend', zh: 'CPI 趋势' },
      structural_news: { en: 'Structural News', zh: '结构性新闻' },
    }

    const label = labels[name]
    if (!label) return name
    return language === 'zh' ? label.zh : label.en
  }

  const translateSignalRationale = (name: string, rationale: string) => {
    if (language === 'en') return rationale

    const genericPatterns: Array<[RegExp, (...args: string[]) => string]> = [
      [/^MA5\/MA20 cross signal: (.+)$/, (score) => `MA5 / MA20 交叉信号：${score}`],
      [/^RSI ([\d.]+) — oversold$/, (value) => `RSI ${value}，超卖`],
      [/^RSI ([\d.]+) — approaching oversold$/, (value) => `RSI ${value}，接近超卖`],
      [/^RSI ([\d.]+) — neutral$/, (value) => `RSI ${value}，中性`],
      [/^RSI ([\d.]+) — approaching overbought$/, (value) => `RSI ${value}，接近超买`],
      [/^RSI ([\d.]+) — overbought$/, (value) => `RSI ${value}，超买`],
      [/^MACD histogram ([\d.+-]+), rising$/, (value) => `MACD 柱状图 ${value}，上升中`],
      [/^MACD histogram ([\d.+-]+), falling$/, (value) => `MACD 柱状图 ${value}，下降中`],
      [/^Bollinger %B = ([\d.+-]+)$/, (value) => `布林带 %B = ${value}`],
      [/^ATR ([\d.]+) — high volatility \(([\d.]+)x median\)$/, (atr, ratio) => `ATR ${atr}，高波动（为中位数的 ${ratio} 倍）`],
      [/^ATR ([\d.]+) — low volatility \(([\d.]+)x median\)$/, (atr, ratio) => `ATR ${atr}，低波动（为中位数的 ${ratio} 倍）`],
      [/^ATR ([\d.]+) — normal volatility \(([\d.]+)x median\)$/, (atr, ratio) => `ATR ${atr}，波动正常（为中位数的 ${ratio} 倍）`],
      [/^ATR ([\d.]+) — normal volatility$/, (atr) => `ATR ${atr}，波动正常`],
      [/^OBV slope ([\d.+-]+), price up$/, (value) => `OBV 斜率 ${value}，价格上涨`],
      [/^OBV slope ([\d.+-]+), price down$/, (value) => `OBV 斜率 ${value}，价格下跌`],
      [/^Volume ([\d.]+)x average, price up$/, (value) => `成交量为均值的 ${value} 倍，价格上涨`],
      [/^Volume ([\d.]+)x average, price down$/, (value) => `成交量为均值的 ${value} 倍，价格下跌`],
      [/^5d momentum at (.+) percentile$/, (value) => `5日动量位于 ${value} 分位`],
      [/^24h news sentiment: ([\d.+-]+) across (\d+) articles$/, (value, count) => `24小时新闻情绪：${value}，共 ${count} 篇文章`],
      [/^24h news sentiment: ([\d.+-]+)$/, (value) => `24小时新闻情绪：${value}`],
      [/^No news in the last 24h$/, () => '最近24小时无新闻'],
      [/^News volume z-score: ([\d.+-]+) \(non-directional\) — ELEVATED$/, (value) => `新闻数量 Z-Score：${value}，非方向性，明显偏高`],
      [/^News volume z-score: ([\d.+-]+) \(non-directional\)$/, (value) => `新闻数量 Z-Score：${value}，非方向性`],
      [/^News volume z-score: ([\d.+-]+) — ELEVATED$/, (value) => `新闻数量 Z-Score：${value}，明显偏高`],
      [/^News volume z-score: ([\d.+-]+)$/, (value) => `新闻数量 Z-Score：${value}`],
      [/^MA50=([\d.]+) vs MA200=([\d.]+)$/, (ma50, ma200) => `MA50=${ma50}，MA200=${ma200}`],
      [/^Price ([+\-]?\d+(?:\.\d+)?)% from MA200$/, (value) => `价格相对 MA200 偏离 ${value}%`],
      [/^52-week position: (.+)$/, (value) => `52周位置：${value}`],
      [/^Relative strength vs SPY \((3m)\): ([+\-]?\d+(?:\.\d+)?)%$/, (_period, value) => `相对 SPY 强弱（3个月）：${value}%`],
      [/^Relative strength vs SPY \((6m)\): ([+\-]?\d+(?:\.\d+)?)%$/, (_period, value) => `相对 SPY 强弱（6个月）：${value}%`],
      [/^Earnings growth: ([+\-]?\d+(?:\.\d+)?)%$/, (value) => `利润增长：${value}%`],
      [/^Revenue growth: ([+\-]?\d+(?:\.\d+)?)%$/, (value) => `营收增长：${value}%`],
      [/^Volatility expanding ([+\-]?\d+)% from 2-month avg$/, (value) => `波动率较两个月均值扩大 ${value}%`],
      [/^Volatility contracting ([+\-]?\d+)%$/, (value) => `波动率收缩 ${value}%`],
      [/^Volatility stable \(([+\-]?\d+)%\)$/, (value) => `波动率稳定（${value}%）`],
      [/^Trailing P\/E = ([\d.]+)$/, (value) => `静态市盈率 = ${value}`],
      [/^P\/B = ([\d.]+)$/, (value) => `市净率 = ${value}`],
      [/^PEG = ([\d.]+)$/, (value) => `PEG = ${value}`],
      [/^EV\/EBITDA = ([\d.]+)$/, (value) => `EV/EBITDA = ${value}`],
      [/^ROE = ([+\-]?\d+(?:\.\d+)?)%$/, (value) => `ROE = ${value}%`],
      [/^Profit margin: ([+\-]?\d+(?:\.\d+)?)%$/, (value) => `利润率：${value}%`],
      [/^D\/E ratio = ([\d.]+)%$/, (value) => `债务 / 权益比 = ${value}%`],
      [/^Yield curve score: (.+)$/, (value) => `收益率曲线评分：${value}`],
      [/^Fed cycle score: (.+)$/, (value) => `联储周期评分：${value}`],
      [/^CPI trend score: (.+)$/, (value) => `CPI 趋势评分：${value}`],
      [/^Structural events: (.+)$/, (value) => `结构性事件：${value}`],
    ]

    return replacePatterns(rationale, genericPatterns)
  }

  return (
    <I18nContext.Provider
      value={{
        language,
        setLanguage,
        toggleLanguage: () => setLanguage((current) => (current === 'en' ? 'zh' : 'en')),
        locale,
        t,
        formatDate,
        formatDateTime,
        formatVerdict,
        translateProgress,
        translateCaveat,
        translateSignalName,
        translateSignalRationale,
      }}
    >
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider')
  }
  return context
}
