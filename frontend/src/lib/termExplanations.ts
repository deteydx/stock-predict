import type { Language } from '../i18n'
import type { Signal } from '../types'

export type FundamentalMetricKey =
  | 'market_cap'
  | 'pe_trailing'
  | 'pe_forward'
  | 'pb'
  | 'peg'
  | 'ev_ebitda'
  | 'roe'
  | 'profit_margin'
  | 'revenue_growth'
  | 'earnings_growth'
  | 'debt_to_equity'
  | 'free_cash_flow'
  | 'dividend_yield'
  | 'beta'

export interface ResolvedTermExplanation {
  calculation: string
  meaning: string
  interpretation: string
  current: string | null
}

interface ExplainOptions {
  language: Language
  locale: string
}

function copy(language: Language, en: string, zh: string) {
  return language === 'zh' ? zh : en
}

function decimal(value: number, locale: string, digits = 2) {
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)
}

function integer(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 0,
  }).format(value)
}

function compactUsd(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

function usd(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

function percent(value: number, locale: string, digits = 1) {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)
}

function signedPercent(value: number, locale: string, digits = 1) {
  const body = percent(Math.abs(value), locale, digits)
  if (value > 0) return `+${body}`
  if (value < 0) return `-${body}`
  return percent(0, locale, digits)
}

function score(score: number) {
  return score > 0 ? `+${score}` : String(score)
}

function resolveFundamentalCurrent(
  key: FundamentalMetricKey,
  value: number | null,
  { language, locale }: ExplainOptions
) {
  if (value == null) return null

  switch (key) {
    case 'market_cap':
      if (value >= 200e9) {
        return copy(
          language,
          `Current market cap is ${compactUsd(value, locale)}, which puts the company in mega-cap territory.`,
          `当前市值约为 ${compactUsd(value, locale)}，属于超大盘公司。`
        )
      }
      if (value >= 10e9) {
        return copy(
          language,
          `Current market cap is ${compactUsd(value, locale)}, broadly in large-cap territory.`,
          `当前市值约为 ${compactUsd(value, locale)}，大致属于大盘股。`
        )
      }
      if (value >= 2e9) {
        return copy(
          language,
          `Current market cap is ${compactUsd(value, locale)}, closer to mid-cap size.`,
          `当前市值约为 ${compactUsd(value, locale)}，更接近中盘股体量。`
        )
      }
      return copy(
        language,
        `Current market cap is ${compactUsd(value, locale)}, which is relatively small and usually comes with higher business volatility.`,
        `当前市值约为 ${compactUsd(value, locale)}，体量相对较小，通常伴随更高经营波动。`
      )
    case 'pe_trailing':
    case 'pe_forward':
      if (value <= 0) {
        return copy(
          language,
          'The current P/E is non-positive, which usually means earnings are weak or negative and the ratio is less informative.',
          '当前市盈率为非正值，通常意味着盈利较弱或为负，指标解释力会下降。'
        )
      }
      if (value < 15) {
        return copy(
          language,
          `Current P/E is ${decimal(value, locale)}, which is on the lower side.`,
          `当前市盈率为 ${decimal(value, locale)}，处于相对偏低区间。`
        )
      }
      if (value < 30) {
        return copy(
          language,
          `Current P/E is ${decimal(value, locale)}, roughly in a middle range.`,
          `当前市盈率为 ${decimal(value, locale)}，大致处于中间区间。`
        )
      }
      return copy(
        language,
        `Current P/E is ${decimal(value, locale)}, which is relatively elevated and implies stronger growth expectations.`,
        `当前市盈率为 ${decimal(value, locale)}，相对偏高，通常反映市场给了更强的增长预期。`
      )
    case 'pb':
      if (value < 1) {
        return copy(
          language,
          `Current P/B is ${decimal(value, locale)}, below 1, which often signals deep value, asset-heavy pricing, or stress.`,
          `当前市净率为 ${decimal(value, locale)}，低于 1，常见于深度价值、重资产定价或压力情形。`
        )
      }
      if (value < 3) {
        return copy(
          language,
          `Current P/B is ${decimal(value, locale)}, a moderate range for many sectors.`,
          `当前市净率为 ${decimal(value, locale)}，对很多行业来说属于中等区间。`
        )
      }
      return copy(
        language,
        `Current P/B is ${decimal(value, locale)}, which is relatively rich versus book value.`,
        `当前市净率为 ${decimal(value, locale)}，相对账面价值来看偏贵。`
      )
    case 'peg':
      if (value < 0) {
        return copy(
          language,
          `Current PEG is ${decimal(value, locale)}, below zero, which usually reflects negative expected growth.`,
          `当前 PEG 为 ${decimal(value, locale)}，小于 0，通常意味着预期增长为负。`
        )
      }
      if (value < 1) {
        return copy(
          language,
          `Current PEG is ${decimal(value, locale)}, which is attractive if the growth forecast is reliable.`,
          `当前 PEG 为 ${decimal(value, locale)}，如果增长预测可信，一般算比较有吸引力。`
        )
      }
      if (value < 2) {
        return copy(
          language,
          `Current PEG is ${decimal(value, locale)}, broadly a balanced range.`,
          `当前 PEG 为 ${decimal(value, locale)}，大致属于相对均衡的区间。`
        )
      }
      return copy(
        language,
        `Current PEG is ${decimal(value, locale)}, which is on the expensive side relative to growth.`,
        `当前 PEG 为 ${decimal(value, locale)}，相对于增长来说偏贵。`
      )
    case 'ev_ebitda':
      if (value < 8) {
        return copy(
          language,
          `Current EV/EBITDA is ${decimal(value, locale)}, which is relatively low.`,
          `当前 EV/EBITDA 为 ${decimal(value, locale)}，相对偏低。`
        )
      }
      if (value < 14) {
        return copy(
          language,
          `Current EV/EBITDA is ${decimal(value, locale)}, around a mid-range level.`,
          `当前 EV/EBITDA 为 ${decimal(value, locale)}，大致属于中等区间。`
        )
      }
      return copy(
        language,
        `Current EV/EBITDA is ${decimal(value, locale)}, which is relatively elevated.`,
        `当前 EV/EBITDA 为 ${decimal(value, locale)}，相对偏高。`
      )
    case 'roe':
      if (value < 0.05) {
        return copy(
          language,
          `Current ROE is ${percent(value, locale)}, which is weak.`,
          `当前 ROE 为 ${percent(value, locale)}，偏弱。`
        )
      }
      if (value < 0.15) {
        return copy(
          language,
          `Current ROE is ${percent(value, locale)}, which is acceptable but not exceptional.`,
          `当前 ROE 为 ${percent(value, locale)}，尚可，但不算特别强。`
        )
      }
      if (value < 0.2) {
        return copy(
          language,
          `Current ROE is ${percent(value, locale)}, which is strong.`,
          `当前 ROE 为 ${percent(value, locale)}，表现较强。`
        )
      }
      return copy(
        language,
        `Current ROE is ${percent(value, locale)}, which is very strong, though leverage should also be checked.`,
        `当前 ROE 为 ${percent(value, locale)}，非常强，但也要结合杠杆一起看。`
      )
    case 'profit_margin':
      if (value < 0) {
        return copy(
          language,
          `Current margin is ${percent(value, locale)}, meaning the company is losing money at the net level.`,
          `当前利润率为 ${percent(value, locale)}，说明公司净利润层面仍在亏损。`
        )
      }
      if (value < 0.1) {
        return copy(
          language,
          `Current margin is ${percent(value, locale)}, which is positive but thin.`,
          `当前利润率为 ${percent(value, locale)}，虽然为正，但相对偏薄。`
        )
      }
      if (value < 0.2) {
        return copy(
          language,
          `Current margin is ${percent(value, locale)}, which is healthy.`,
          `当前利润率为 ${percent(value, locale)}，属于比较健康的水平。`
        )
      }
      return copy(
        language,
        `Current margin is ${percent(value, locale)}, which is very strong.`,
        `当前利润率为 ${percent(value, locale)}，非常强。`
      )
    case 'revenue_growth':
    case 'earnings_growth':
      if (value < 0) {
        return copy(
          language,
          `Current growth is ${percent(value, locale)}, which means the line item is contracting.`,
          `当前增速为 ${percent(value, locale)}，说明该指标正在收缩。`
        )
      }
      if (value < 0.08) {
        return copy(
          language,
          `Current growth is ${percent(value, locale)}, which is positive but modest.`,
          `当前增速为 ${percent(value, locale)}，为正但偏温和。`
        )
      }
      if (value < 0.2) {
        return copy(
          language,
          `Current growth is ${percent(value, locale)}, which is healthy.`,
          `当前增速为 ${percent(value, locale)}，属于比较健康的增长。`
        )
      }
      return copy(
        language,
        `Current growth is ${percent(value, locale)}, which is fast.`,
        `当前增速为 ${percent(value, locale)}，属于较快增长。`
      )
    case 'debt_to_equity':
      if (value < 50) {
        return copy(
          language,
          `Current debt/equity is ${decimal(value, locale, 1)} in yfinance's percentage-style format, which is conservative.`,
          `当前负债权益比为 ${decimal(value, locale, 1)}（yfinance 的百分比口径），杠杆相对保守。`
        )
      }
      if (value < 100) {
        return copy(
          language,
          `Current debt/equity is ${decimal(value, locale, 1)}, which is manageable.`,
          `当前负债权益比为 ${decimal(value, locale, 1)}，属于可控杠杆。`
        )
      }
      if (value < 200) {
        return copy(
          language,
          `Current debt/equity is ${decimal(value, locale, 1)}, which is already leveraged.`,
          `当前负债权益比为 ${decimal(value, locale, 1)}，已经有明显杠杆。`
        )
      }
      return copy(
        language,
        `Current debt/equity is ${decimal(value, locale, 1)}, which is high leverage.`,
        `当前负债权益比为 ${decimal(value, locale, 1)}，杠杆偏高。`
      )
    case 'free_cash_flow':
      if (value < 0) {
        return copy(
          language,
          `Current free cash flow is ${compactUsd(value, locale)}, which means the business is burning cash after capital spending.`,
          `当前自由现金流约为 ${compactUsd(value, locale)}，说明资本开支后仍在消耗现金。`
        )
      }
      return copy(
        language,
        `Current free cash flow is ${compactUsd(value, locale)}, which means the business is generating cash after capital spending.`,
        `当前自由现金流约为 ${compactUsd(value, locale)}，说明资本开支后仍能净产生现金。`
      )
    case 'dividend_yield':
      if (value <= 0) {
        return copy(
          language,
          'Current dividend yield is effectively zero, so returns rely mainly on price appreciation.',
          '当前股息率基本为 0，投资回报主要依赖股价上涨。'
        )
      }
      if (value < 0.03) {
        return copy(
          language,
          `Current dividend yield is ${percent(value, locale)}, which is modest.`,
          `当前股息率为 ${percent(value, locale)}，属于温和水平。`
        )
      }
      if (value < 0.06) {
        return copy(
          language,
          `Current dividend yield is ${percent(value, locale)}, which is relatively high.`,
          `当前股息率为 ${percent(value, locale)}，相对较高。`
        )
      }
      return copy(
        language,
        `Current dividend yield is ${percent(value, locale)}, which is very high and should be checked for sustainability.`,
        `当前股息率为 ${percent(value, locale)}，非常高，需要核查可持续性。`
      )
    case 'beta':
      if (value < 0.8) {
        return copy(
          language,
          `Current beta is ${decimal(value, locale)}, which is lower-volatility than the market.`,
          `当前 Beta 为 ${decimal(value, locale)}，波动通常低于大盘。`
        )
      }
      if (value < 1.2) {
        return copy(
          language,
          `Current beta is ${decimal(value, locale)}, broadly in line with the market.`,
          `当前 Beta 为 ${decimal(value, locale)}，整体与大盘波动接近。`
        )
      }
      return copy(
        language,
        `Current beta is ${decimal(value, locale)}, which implies above-market volatility.`,
        `当前 Beta 为 ${decimal(value, locale)}，意味着波动通常高于大盘。`
      )
  }
}

export function resolveFundamentalExplanation(
  key: FundamentalMetricKey,
  value: number | null,
  options: ExplainOptions
): ResolvedTermExplanation {
  const { language } = options

  const current = resolveFundamentalCurrent(key, value, options)

  switch (key) {
    case 'market_cap':
      return {
        calculation: copy(
          language,
          'Market cap is share price multiplied by shares outstanding. In this app it comes from yfinance as the latest `marketCap` snapshot.',
          '市值等于股价乘以总股本。这个页面里显示的是 yfinance 返回的最新 `marketCap` 快照。'
        ),
        meaning: copy(
          language,
          'It measures company size. Larger companies are usually more liquid and diversified; smaller ones can move faster but carry more business risk.',
          '它衡量公司的体量。大公司通常流动性更好、业务更分散；小公司弹性更大，但经营风险通常也更高。'
        ),
        interpretation: copy(
          language,
          'Higher market cap usually means more maturity and stability, not necessarily better returns. Lower market cap often means more upside and more volatility.',
          '市值高通常意味着更成熟、更稳定，但不代表回报一定更好；市值低往往意味着更高弹性，也意味着更高波动。'
        ),
        current,
      }
    case 'pe_trailing':
      return {
        calculation: copy(
          language,
          'Trailing P/E = current share price divided by trailing 12-month earnings per share.',
          '静态市盈率 = 当前股价 ÷ 过去 12 个月每股收益。'
        ),
        meaning: copy(
          language,
          'It shows how much investors are paying for the company’s already-earned profits.',
          '它表示市场愿意为公司已经实现的利润支付多少倍价格。'
        ),
        interpretation: copy(
          language,
          'Lower values can mean cheaper valuation or weak expectations. Higher values can mean strong growth expectations, overvaluation, or temporarily depressed earnings.',
          '数值低可能意味着估值便宜，也可能是市场预期差；数值高可能反映高增长预期、估值偏贵，或者利润暂时偏低。'
        ),
        current,
      }
    case 'pe_forward':
      return {
        calculation: copy(
          language,
          'Forward P/E = current share price divided by expected next-12-month earnings per share.',
          '动态市盈率 = 当前股价 ÷ 未来 12 个月预期每股收益。'
        ),
        meaning: copy(
          language,
          'It prices the stock against forecast earnings instead of historical earnings.',
          '它用未来盈利预测来给股票定价，而不是用历史盈利。'
        ),
        interpretation: copy(
          language,
          'Lower forward P/E can mean the stock looks cheap if forecasts hold. Higher forward P/E means investors are paying more for expected future growth.',
          '动态市盈率低，说明如果盈利预测成立，股票可能更便宜；动态市盈率高，说明市场愿意为未来增长支付更高价格。'
        ),
        current,
      }
    case 'pb':
      return {
        calculation: copy(
          language,
          'P/B = market value per share divided by book value per share.',
          '市净率 = 每股市值 ÷ 每股净资产。'
        ),
        meaning: copy(
          language,
          'It compares the market’s valuation to the accounting value of shareholders’ equity.',
          '它把市场给出的估值和账面净资产做比较。'
        ),
        interpretation: copy(
          language,
          'Lower P/B can suggest asset-based value or distress. Higher P/B means the market prices the business well above book value, often because it expects high returns on capital.',
          '市净率低可能意味着资产型价值机会，也可能意味着公司承压；市净率高表示市场给的价格明显高于账面价值，往往说明市场预期公司有较高资本回报。'
        ),
        current,
      }
    case 'peg':
      return {
        calculation: copy(
          language,
          'PEG = P/E divided by expected earnings growth rate.',
          'PEG = 市盈率 ÷ 预期利润增长率。'
        ),
        meaning: copy(
          language,
          'It adjusts valuation for growth, so you can ask whether the price paid is justified by expected earnings expansion.',
          '它把估值和增长放在一起看，用来判断当前价格是否被未来利润增长支撑。'
        ),
        interpretation: copy(
          language,
          'Below 1 is often seen as attractive, around 1 to 2 is more balanced, and above 2 to 3 can start to look expensive. Negative PEG usually means growth is negative.',
          'PEG 低于 1 通常较有吸引力，1 到 2 更偏均衡，超过 2 到 3 往往开始显得偏贵。PEG 为负通常说明增长为负。'
        ),
        current,
      }
    case 'ev_ebitda':
      return {
        calculation: copy(
          language,
          'EV/EBITDA = enterprise value divided by EBITDA. Enterprise value includes equity plus net debt.',
          'EV/EBITDA = 企业价值 ÷ EBITDA。企业价值包含股权价值和净负债。'
        ),
        meaning: copy(
          language,
          'It values the whole business before capital structure and non-cash accounting effects.',
          '它从企业整体角度估值，弱化资本结构和部分非现金会计项目的影响。'
        ),
        interpretation: copy(
          language,
          'Lower values can indicate cheaper operating valuation. Higher values often mean premium expectations or lower current EBITDA.',
          '数值低通常表示经营层面估值更便宜；数值高往往代表市场给了溢价预期，或者当前 EBITDA 偏低。'
        ),
        current,
      }
    case 'roe':
      return {
        calculation: copy(
          language,
          'ROE = net income divided by shareholders’ equity.',
          'ROE = 净利润 ÷ 股东权益。'
        ),
        meaning: copy(
          language,
          'It shows how efficiently management turns shareholder capital into profit.',
          '它衡量公司把股东投入资本转化为利润的效率。'
        ),
        interpretation: copy(
          language,
          'Higher ROE is usually better, but it can be artificially boosted by heavy leverage or very low equity.',
          'ROE 越高通常越好，但如果杠杆很高或净资产很低，也可能被“抬高”。'
        ),
        current,
      }
    case 'profit_margin':
      return {
        calculation: copy(
          language,
          'Profit margin = net income divided by revenue.',
          '利润率 = 净利润 ÷ 营收。'
        ),
        meaning: copy(
          language,
          'It shows how much of each revenue dollar remains as profit after costs, expenses, interest, and taxes.',
          '它表示每 1 美元营收最终能留下多少净利润。'
        ),
        interpretation: copy(
          language,
          'Higher margins imply stronger pricing power, efficiency, or business quality. Very low or negative margins mean the business has little room for error.',
          '利润率高通常说明定价权、经营效率或商业模式更强；利润率很低或为负说明公司抗风险空间更小。'
        ),
        current,
      }
    case 'revenue_growth':
      return {
        calculation: copy(
          language,
          'Revenue growth is the year-over-year growth rate reported by yfinance for the latest period it exposes.',
          '营收增长率是 yfinance 提供的最新一期同比营收增速。'
        ),
        meaning: copy(
          language,
          'It measures whether the company is still expanding its top line.',
          '它衡量公司的收入规模是否仍在扩张。'
        ),
        interpretation: copy(
          language,
          'Higher revenue growth often supports premium valuations, but it matters whether growth is durable and profitable. Negative growth means the top line is shrinking.',
          '更高的营收增长通常能支撑更高估值，但关键在于增长是否可持续、是否能转化成利润。负增长说明收入在收缩。'
        ),
        current,
      }
    case 'earnings_growth':
      return {
        calculation: copy(
          language,
          'Earnings growth is the year-over-year profit growth rate provided by yfinance for the latest reported period.',
          '利润增长率是 yfinance 提供的最新一期同比利润增速。'
        ),
        meaning: copy(
          language,
          'It shows whether bottom-line profit is compounding or shrinking.',
          '它衡量公司最终利润是在加速增长还是在收缩。'
        ),
        interpretation: copy(
          language,
          'Higher earnings growth is usually a strong positive, but large jumps can come from one-off effects. Negative earnings growth means profit is deteriorating.',
          '利润增长越高通常越积极，但大幅跳升也可能来自一次性因素；负增长说明盈利能力在恶化。'
        ),
        current,
      }
    case 'debt_to_equity':
      return {
        calculation: copy(
          language,
          'Debt/Equity compares total debt to shareholder equity. In yfinance this field often comes in a percentage-style format, so 50 roughly means 0.5x.',
          '负债权益比比较的是总负债和股东权益。yfinance 里这个字段常用百分比口径，所以 50 大致对应 0.5 倍。'
        ),
        meaning: copy(
          language,
          'It measures how much leverage the business is using.',
          '它衡量公司使用了多少财务杠杆。'
        ),
        interpretation: copy(
          language,
          'Lower values mean a cleaner balance sheet and more flexibility. Higher values can boost returns in good times but increase fragility when business slows.',
          '数值低说明资产负债表更干净、财务弹性更大；数值高在景气时能放大回报，但在经营放缓时也会放大风险。'
        ),
        current,
      }
    case 'free_cash_flow':
      return {
        calculation: copy(
          language,
          'Free cash flow is operating cash flow minus capital expenditures.',
          '自由现金流 = 经营现金流 - 资本开支。'
        ),
        meaning: copy(
          language,
          'It measures how much cash the company can keep after maintaining and expanding the business.',
          '它衡量公司在维持和扩张经营之后，最终还能留下多少现金。'
        ),
        interpretation: copy(
          language,
          'Positive and growing free cash flow is usually a sign of quality. Negative free cash flow is not always bad for fast-growing firms, but it raises funding risk.',
          '自由现金流持续为正且增长，通常是高质量特征；自由现金流为负对高速成长公司不一定是坏事，但会提高融资依赖和风险。'
        ),
        current,
      }
    case 'dividend_yield':
      return {
        calculation: copy(
          language,
          'Dividend yield = annual dividend per share divided by current share price.',
          '股息率 = 每股年度分红 ÷ 当前股价。'
        ),
        meaning: copy(
          language,
          'It measures the cash income an investor receives from dividends, excluding price changes.',
          '它衡量投资者仅从分红获得的现金回报，不含股价涨跌。'
        ),
        interpretation: copy(
          language,
          'A higher yield can be attractive for income, but extremely high yields can also warn that the market expects the dividend to be cut.',
          '股息率高对收息型投资者更有吸引力，但极高的股息率也可能在提示市场担心未来削减分红。'
        ),
        current,
      }
    case 'beta':
      return {
        calculation: copy(
          language,
          'Beta measures how sensitive the stock has been relative to the market, usually versus a broad benchmark.',
          'Beta 衡量的是股票相对大盘的历史波动敏感度，通常对标广义市场指数。'
        ),
        meaning: copy(
          language,
          'It helps estimate how violently the stock may move when the market moves.',
          '它帮助判断当大盘波动时，这只股票可能会跟着放大还是收缩波动。'
        ),
        interpretation: copy(
          language,
          'Beta near 1 means market-like volatility. Above 1 means more volatile than the market. Below 1 means more defensive.',
          'Beta 接近 1 说明波动接近大盘；高于 1 表示波动更大；低于 1 表示相对防御。'
        ),
        current,
      }
  }
}

export function resolveSignalExplanation(
  signal: Signal,
  { language, locale }: ExplainOptions
): ResolvedTermExplanation | null {
  switch (signal.name) {
    case 'ma_cross':
      return {
        calculation: copy(
          language,
          'The backend calculates SMA5 and SMA20 from daily closes. Score = +2 when SMA5 crosses above SMA20, +1 when it stays above, -1 when it stays below, and -2 when it crosses below.',
          '后端会根据日收盘价计算 SMA5 和 SMA20。评分规则是：SMA5 上穿 SMA20 记 +2，持续在上方记 +1，持续在下方记 -1，下穿记 -2。'
        ),
        meaning: copy(
          language,
          'It measures very short-term trend alignment.',
          '它衡量的是非常短线的趋势方向是否一致。'
        ),
        interpretation: copy(
          language,
          'Higher values are bullish, lower values are bearish. Fresh crosses (+2/-2) are stronger than a simple above/below state (+1/-1).',
          '分数越高越偏多，越低越偏空。刚发生的均线交叉（+2/-2）比单纯位于上方或下方（+1/-1）更强。'
        ),
        current: copy(
          language,
          {
            '2': 'Current reading is +2: a fresh bullish 5/20-day cross.',
            '1': 'Current reading is +1: MA5 is above MA20, but not on a fresh cross day.',
            '0': 'Current reading is 0: no usable signal.',
            '-1': 'Current reading is -1: MA5 is below MA20.',
            '-2': 'Current reading is -2: a fresh bearish 5/20-day cross.',
          }[String(signal.score)] ?? `Current reading is ${score(signal.score)}.`,
          {
            '2': '当前读数为 +2：5 日均线刚刚上穿 20 日均线。',
            '1': '当前读数为 +1：5 日均线位于 20 日均线上方，但不是刚发生交叉。',
            '0': '当前读数为 0：暂无有效信号。',
            '-1': '当前读数为 -1：5 日均线位于 20 日均线下方。',
            '-2': '当前读数为 -2：5 日均线刚刚下穿 20 日均线。',
          }[String(signal.score)] ?? `当前读数为 ${score(signal.score)}。`
        ),
      }
    case 'rsi':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'RSI(14) compares average up moves and down moves over 14 periods and rescales the result to 0-100.',
          'RSI(14) 会比较最近 14 个周期内平均上涨幅度和平均下跌幅度，并把结果缩放到 0 到 100。'
        ),
        meaning: copy(
          language,
          'It measures short-term momentum and whether price is stretched.',
          '它衡量短线动量是否过热或过冷。'
        ),
        interpretation: copy(
          language,
          'In this short-term model it is used contrarian-style: below 30 is treated as oversold and bullish for mean reversion, above 70 as overbought and bearish.',
          '在这个短线模型里，RSI 采用偏逆向的解读：低于 30 视为超卖，偏向均值回归式看多；高于 70 视为超买，偏向看空。'
        ),
        current: copy(
          language,
          `Current RSI is ${decimal(signal.value, locale, 1)}. The model maps it to score ${score(signal.score)} using the 30 / 45 / 55 / 70 cutoffs.`,
          `当前 RSI 为 ${decimal(signal.value, locale, 1)}。模型按 30 / 45 / 55 / 70 这几个阈值把它映射为 ${score(signal.score)} 分。`
        ),
      }
    case 'macd':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'MACD uses EMA12 minus EMA26. The histogram is MACD minus its 9-period signal line. The model also checks whether the histogram is rising or falling.',
          'MACD 由 EMA12 减去 EMA26 得到，柱状图则是 MACD 线减去 9 周期信号线。模型还会判断柱状图是在走高还是走低。'
        ),
        meaning: copy(
          language,
          'It measures trend momentum and whether bullish or bearish momentum is accelerating.',
          '它衡量趋势动量，以及多头或空头动量是在增强还是减弱。'
        ),
        interpretation: copy(
          language,
          'Positive and rising histogram is strongest bullish (+2). Negative and falling is strongest bearish (-2). Values around zero are weak or transitionary.',
          '柱状图为正且继续走高时最偏多（+2）；为负且继续走低时最偏空（-2）；接近 0 时通常处于弱趋势或切换阶段。'
        ),
        current: copy(
          language,
          `Current histogram is ${decimal(signal.value, locale, 4)} and the rule score is ${score(signal.score)}.`,
          `当前 MACD 柱状图为 ${decimal(signal.value, locale, 4)}，规则评分为 ${score(signal.score)}。`
        ),
      }
    case 'bollinger':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'Bollinger %B = (price - lower band) / (upper band - lower band), using a 20-day moving average and bands at 2 standard deviations.',
          '布林带 %B = （价格 - 下轨）÷（上轨 - 下轨），这里使用 20 日均线和 2 倍标准差带宽。'
        ),
        meaning: copy(
          language,
          'It shows where price sits within or outside the Bollinger Band channel.',
          '它表示当前价格位于布林带通道的什么位置。'
        ),
        interpretation: copy(
          language,
          'In this model, values below 0 are most bullish as price is below the lower band, 0 to 0.2 is mildly bullish, 0.8 to 1 is mildly bearish, and above 1 is most bearish.',
          '在这个模型里，%B 低于 0 最偏多，因为价格跌到下轨外；0 到 0.2 轻度偏多；0.8 到 1 轻度偏空；高于 1 最偏空。'
        ),
        current: copy(
          language,
          `Current Bollinger %B is ${decimal(signal.value, locale, 2)}, which the model converts to score ${score(signal.score)}.`,
          `当前布林带 %B 为 ${decimal(signal.value, locale, 2)}，模型据此给出 ${score(signal.score)} 分。`
        ),
      }
    case 'atr_regime':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'ATR(14) is divided by the median ATR over the last 252 trading days when available. That ratio is the displayed value.',
          '模型会先计算 ATR(14)，再除以最近 252 个交易日的 ATR 中位数；显示出来的就是这个比值。'
        ),
        meaning: copy(
          language,
          'It measures whether the stock is in a high-volatility or low-volatility regime.',
          '它衡量当前股票是否处在高波动或低波动环境。'
        ),
        interpretation: copy(
          language,
          'Above 1.5x the historical median is treated as a riskier high-volatility state and scores -1. Below 0.7x is calmer and scores +1.',
          '高于历史中位数 1.5 倍会被视为高波动、风险偏大的状态，记 -1；低于 0.7 倍代表更平稳，记 +1。'
        ),
        current: copy(
          language,
          `Current ATR regime is ${decimal(signal.value, locale, 2)}x the median, so the rule score is ${score(signal.score)}.`,
          `当前 ATR 状态为历史中位数的 ${decimal(signal.value, locale, 2)} 倍，因此规则评分为 ${score(signal.score)}。`
        ),
      }
    case 'obv_trend':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'OBV accumulates signed volume. The model fits a 20-day linear-regression slope to OBV, compares it with 20-day price direction, and checks divergence at multiple offsets.',
          'OBV 会把上涨日的成交量累加、下跌日的成交量扣减。模型再对最近 20 天 OBV 做线性回归斜率，并拿它和 20 天价格方向及多个偏移点的背离情况一起判断。'
        ),
        meaning: copy(
          language,
          'It asks whether volume flow is confirming the move or diverging from price.',
          '它用来判断成交量是在确认价格走势，还是和价格发生背离。'
        ),
        interpretation: copy(
          language,
          'Positive OBV with falling price can be bullish divergence. Negative OBV with rising price can be bearish divergence. Confirmed divergences get stronger scores.',
          '当 OBV 向上但价格下跌时，可能是多头背离；当 OBV 向下但价格上涨时，可能是空头背离。背离确认越充分，评分越极端。'
        ),
        current: copy(
          language,
          `Current OBV slope is ${integer(signal.value, locale)} and the model assigns score ${score(signal.score)} based on confirmation or divergence.`,
          `当前 OBV 斜率为 ${integer(signal.value, locale)}，模型会结合确认或背离情况给出 ${score(signal.score)} 分。`
        ),
      }
    case 'volume_spike':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'Displayed value = today’s volume divided by the 20-day average volume.',
          '显示值 = 当日成交量 ÷ 20 日平均成交量。'
        ),
        meaning: copy(
          language,
          'It measures whether the latest price move happened on unusually heavy participation.',
          '它衡量最新价格波动是否伴随着异常放大的参与度。'
        ),
        interpretation: copy(
          language,
          'In this model only spikes above 2x matter directionally. Heavy volume on an up day scores +1; heavy volume on a down day scores -1.',
          '在这个模型里，只有超过 2 倍均量的放量才会产生方向性影响。放量上涨记 +1，放量下跌记 -1。'
        ),
        current: copy(
          language,
          `Current volume is ${decimal(signal.value, locale, 1)}x the 20-day average, producing score ${score(signal.score)}.`,
          `当前成交量是 20 日均量的 ${decimal(signal.value, locale, 1)} 倍，因此得到 ${score(signal.score)} 分。`
        ),
      }
    case 'momentum_5d':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The backend computes 5-day return and ranks the latest value against the last 252 trading days. The displayed value is that percentile.',
          '后端先计算 5 日涨跌幅，再把最新值放到过去 252 个交易日里做分位排序；显示值就是这个分位。'
        ),
        meaning: copy(
          language,
          'It measures how strong or weak the recent 5-day move is relative to the stock’s own recent history.',
          '它衡量最近 5 天的走势，相对于这只股票自己过去一年历史，是强还是弱。'
        ),
        interpretation: copy(
          language,
          'This signal is trend-following, not contrarian: above the 80th percentile scores +1, below the 20th percentile scores -1.',
          '这个信号是顺势而不是逆势逻辑：高于 80 分位记 +1，低于 20 分位记 -1。'
        ),
        current: copy(
          language,
          `Current 5-day momentum percentile is ${percent(signal.value, locale, 0)}, so the rule score is ${score(signal.score)}.`,
          `当前 5 日动量分位为 ${percent(signal.value, locale, 0)}，因此规则评分为 ${score(signal.score)}。`
        ),
      }
    case 'support_resistance':
      return {
        calculation: copy(
          language,
          'The backend fuses swing pivots, moving averages, Fibonacci retracements, and volume-profile levels, clusters them with an ATR-based radius, then checks whether price is within 1 ATR of the nearest support or resistance. Strong confluence within 0.5 ATR can add an extra point.',
          '后端会把摆动高低点、移动均线、斐波那契回撤和成交量分布关键位合并起来，再用基于 ATR 的半径做聚类，最后判断当前价格是否位于最近支撑或阻力 1 个 ATR 范围内。若 0.5 个 ATR 内还出现强共振，会额外加减 1 分。'
        ),
        meaning: copy(
          language,
          'It measures whether price is sitting near a likely reaction zone.',
          '它衡量的是当前价格是否正处在潜在的关键反应区域附近。'
        ),
        interpretation: copy(
          language,
          'Higher scores mean nearby support is more relevant than nearby resistance. Lower scores mean overhead resistance is more constraining. Zero means price is roughly between major levels.',
          '分数越高，说明附近支撑比阻力更关键；分数越低，说明上方阻力更压制；0 分通常表示价格大致处于主要区间中间。'
        ),
        current: signal.value == null
          ? null
          : copy(
              language,
              `Current reference price is ${usd(signal.value, locale)} and the level model gives score ${score(signal.score)}.`,
              `当前参考价格为 ${usd(signal.value, locale)}，关口模型给出的评分是 ${score(signal.score)}。`
            ),
      }
    case 'news_sentiment_24h':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The model computes a time-decayed, relevance-weighted average sentiment for news published in the last 24 hours.',
          '模型会对过去 24 小时的新闻情绪做时间衰减和相关性加权平均。'
        ),
        meaning: copy(
          language,
          'It measures whether the recent news flow is net bullish or net bearish.',
          '它衡量最近新闻流整体是偏多还是偏空。'
        ),
        interpretation: copy(
          language,
          'Sentiment above +0.4 scores +2, above +0.08 scores +1, around zero is neutral, below -0.08 turns negative, and below -0.4 is strongly bearish.',
          '情绪值高于 +0.4 记 +2，高于 +0.08 记 +1，接近 0 为中性，低于 -0.08 转负，低于 -0.4 则明显偏空。'
        ),
        current: copy(
          language,
          `Current 24h news sentiment is ${decimal(signal.value, locale, 2)}, producing score ${score(signal.score)}.`,
          `当前 24 小时新闻情绪为 ${decimal(signal.value, locale, 2)}，对应评分 ${score(signal.score)}。`
        ),
      }
    case 'news_volume_zscore':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'This is a z-score: recent 1-day news count versus a 30-day baseline. It is informational and carries zero directional weight.',
          '这是一个 Z-Score：比较最近 1 天的新闻数量与过去 30 天基线的偏离程度。它只做信息提示，不参与方向性加权。'
        ),
        meaning: copy(
          language,
          'It measures whether the stock is drawing unusual headline attention.',
          '它衡量这只股票是否正在吸引异常多的新闻关注。'
        ),
        interpretation: copy(
          language,
          'Higher values mean a news spike. Around 0 is normal. Above 2 usually means attention is clearly elevated, but not necessarily bullish or bearish.',
          '数值越高表示新闻量越异常。接近 0 说明正常；高于 2 通常代表关注度明显升温，但不直接代表利多或利空。'
        ),
        current: copy(
          language,
          `Current news-volume z-score is ${decimal(signal.value, locale, 1)}.`,
          `当前新闻数量 Z-Score 为 ${decimal(signal.value, locale, 1)}。`
        ),
      }
    case 'ma50_ma200':
      return {
        calculation: copy(
          language,
          'The backend calculates SMA50 and SMA200. A fresh golden cross scores +2, remaining above scores +1, remaining below scores -1, and a fresh death cross scores -2.',
          '后端会计算 SMA50 和 SMA200。刚形成金叉记 +2，持续在上方记 +1，持续在下方记 -1，刚形成死叉记 -2。'
        ),
        meaning: copy(
          language,
          'It measures medium-term trend direction.',
          '它衡量的是中期趋势方向。'
        ),
        interpretation: copy(
          language,
          'Higher values mean the medium-term trend is strengthening. Lower values mean the broader trend is weakening.',
          '分数越高表示中期趋势越强，分数越低表示更大级别趋势在走弱。'
        ),
        current: copy(
          language,
          `Current 50/200-day cross score is ${score(signal.score)}.`,
          `当前 50/200 日均线交叉评分为 ${score(signal.score)}。`
        ),
      }
    case 'price_vs_ma200':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'Displayed value = (price - MA200) / MA200.',
          '显示值 = （当前价格 - MA200）÷ MA200。'
        ),
        meaning: copy(
          language,
          'It shows how far price is trading above or below its long-term trend anchor.',
          '它表示当前价格相对长期趋势锚点 MA200 的偏离程度。'
        ),
        interpretation: copy(
          language,
          'Above +10% scores +2, between 0 and +10% scores +1, small dips below MA200 are neutral, and deep breaks below MA200 turn bearish.',
          '高于 MA200 10% 以上记 +2，介于 0 到 +10% 记 +1，略低于 MA200 仍算中性，明显跌破 MA200 后则转为偏空。'
        ),
        current: copy(
          language,
          `Current price is ${signedPercent(signal.value, locale, 1)} away from MA200, so the score is ${score(signal.score)}.`,
          `当前价格相对 MA200 偏离 ${signedPercent(signal.value, locale, 1)}，因此评分为 ${score(signal.score)}。`
        ),
      }
    case 'week52_position':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The backend maps the current price into the last 252 trading days: 0 means the 52-week low, 1 means the 52-week high.',
          '后端会把当前价格映射到最近 252 个交易日区间里：0 代表 52 周低点，1 代表 52 周高点。'
        ),
        meaning: copy(
          language,
          'It shows where the stock sits inside its one-year range.',
          '它表示股票当前位于一年价格区间的哪个位置。'
        ),
        interpretation: copy(
          language,
          'This model reads the signal contrarian-style: near the bottom of the range is more bullish, while near the top is more cautious.',
          '这个模型对它采用偏逆向的解读：越靠近一年区间底部越偏多，越靠近顶部越偏谨慎。'
        ),
        current: copy(
          language,
          `Current 52-week position is ${percent(signal.value, locale, 0)}, giving score ${score(signal.score)}.`,
          `当前 52 周位置为 ${percent(signal.value, locale, 0)}，对应评分 ${score(signal.score)}。`
        ),
      }
    case 'relative_strength_spy':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The backend computes stock return minus SPY return over roughly 3 months (63 days) and 6 months (126 days), then averages the available values.',
          '后端会分别计算股票相对 SPY 约 3 个月（63 天）和 6 个月（126 天）的超额收益，再对可用值取平均。'
        ),
        meaning: copy(
          language,
          'It measures whether the stock is outperforming or lagging the market.',
          '它衡量的是这只股票跑赢还是跑输大盘。'
        ),
        interpretation: copy(
          language,
          'Above +10% is strong outperformance and scores +2. Below -10% is clear underperformance and scores -2.',
          '高于 +10% 属于明显跑赢，记 +2；低于 -10% 属于明显跑输，记 -2。'
        ),
        current: copy(
          language,
          `Current relative strength versus SPY is ${signedPercent(signal.value, locale, 1)}, producing score ${score(signal.score)}.`,
          `当前相对 SPY 的强弱为 ${signedPercent(signal.value, locale, 1)}，对应评分 ${score(signal.score)}。`
        ),
      }
    case 'eps_growth_trend':
    case 'revenue_growth':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          `${signal.name === 'eps_growth_trend' ? 'Earnings' : 'Revenue'} growth comes from the latest yfinance fundamental snapshot and is scored against fixed thresholds.`,
          `${signal.name === 'eps_growth_trend' ? '利润' : '营收'}增长来自最新的 yfinance 基本面快照，并按固定阈值打分。`
        ),
        meaning: copy(
          language,
          `It measures whether ${signal.name === 'eps_growth_trend' ? 'profit' : 'sales'} is expanding fast enough to support the trend.`,
          `它衡量${signal.name === 'eps_growth_trend' ? '利润' : '营收'}增长是否足够支撑当前趋势。`
        ),
        interpretation: copy(
          language,
          `${signal.name === 'eps_growth_trend' ? 'Earnings' : 'Revenue'} growth above the higher threshold scores +2, moderate positive growth is +1 or 0, and negative growth turns bearish.`,
          `${signal.name === 'eps_growth_trend' ? '利润' : '营收'}增长高于较高阈值时记 +2，温和正增长通常是 +1 或 0，负增长则转向偏空。`
        ),
        current: copy(
          language,
          `Current growth is ${percent(signal.value, locale)}, and the medium-term model maps it to score ${score(signal.score)}.`,
          `当前增速为 ${percent(signal.value, locale)}，中期模型据此给出 ${score(signal.score)} 分。`
        ),
      }
    case 'earnings_proximity':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'Displayed value = days until the nearest future earnings date from the earnings calendar.',
          '显示值 = 距离最近一次未来财报日还有多少天，数据来自财报日历。'
        ),
        meaning: copy(
          language,
          'It measures near-term event risk from the next earnings release.',
          '它衡量下一次财报带来的近端事件风险。'
        ),
        interpretation: copy(
          language,
          'Within 7 days the model turns neutral because uncertainty is high. Within 30 days it becomes mildly cautious. More than 30 days away is treated as cleaner for technical trading.',
          '距离财报 7 天以内时，模型会转为中性，因为不确定性很高；30 天以内则偏谨慎；超过 30 天通常认为更适合按技术面交易。'
        ),
        current: copy(
          language,
          `The next earnings event is in ${integer(signal.value, locale)} day(s), so the score is ${score(signal.score)}.`,
          `距离下一次财报还有 ${integer(signal.value, locale)} 天，因此评分为 ${score(signal.score)}。`
        ),
      }
    case 'volatility_regime':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The backend compares the recent 5-day average ATR with an earlier 30-day ATR window from roughly one to two months ago. Displayed value = percentage change.',
          '后端会把最近 5 天 ATR 均值，与大约 1 到 2 个月前那段 30 天 ATR 均值做比较。显示值就是这个变化比例。'
        ),
        meaning: copy(
          language,
          'It measures whether volatility is expanding or contracting.',
          '它衡量波动率是在扩张还是在收缩。'
        ),
        interpretation: copy(
          language,
          'Sharp volatility expansion is mildly bearish because trend reliability drops. Volatility contraction is mildly bullish because price action becomes cleaner.',
          '波动率快速扩张会轻度偏空，因为趋势可靠性下降；波动率收缩会轻度偏多，因为价格行为通常更干净。'
        ),
        current: copy(
          language,
          `Current volatility change is ${signedPercent(signal.value, locale, 0)} versus the earlier baseline, so the score is ${score(signal.score)}.`,
          `当前波动率相对之前基线变化了 ${signedPercent(signal.value, locale, 0)}，因此评分为 ${score(signal.score)}。`
        ),
      }
    case 'sector_etf_trend':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The model looks at the sector ETF mapped to the company’s sector, compares ETF price to its MA50, and checks whether MA50 is rising.',
          '模型会找到该公司所属行业对应的板块 ETF，比较 ETF 当前价格与 MA50 的距离，并检查 MA50 是否在上行。'
        ),
        meaning: copy(
          language,
          'It asks whether the broader sector backdrop is helping or hurting the stock.',
          '它衡量行业环境是在顺风还是逆风。'
        ),
        interpretation: copy(
          language,
          'ETF above a rising MA50 is supportive. ETF below a falling MA50 is a headwind.',
          'ETF 站在上升的 MA50 上方，说明板块环境偏顺风；ETF 跌在下行的 MA50 下方，则说明板块环境偏逆风。'
        ),
        current: copy(
          language,
          `The sector ETF is ${signedPercent(signal.value, locale, 1)} from its MA50, which maps to score ${score(signal.score)}.`,
          `当前行业 ETF 相对 MA50 偏离 ${signedPercent(signal.value, locale, 1)}，对应评分 ${score(signal.score)}。`
        ),
      }
    case 'pe_percentile':
    case 'pb_percentile':
    case 'ev_ebitda':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The raw value shown is the company’s actual ratio. The long-term model then compares it with a sector median and scores the relative ratio: below 0.6x median = +2, below 0.85x = +1, around median = 0, above 1.15x = -1, above 1.5x = -2.',
          '显示的原始数值是公司的实际估值倍数。长期模型会再把它和行业中位数比较：低于中位数 0.6 倍记 +2，低于 0.85 倍记 +1，接近中位数记 0，高于 1.15 倍记 -1，高于 1.5 倍记 -2。'
        ),
        meaning: copy(
          language,
          'It measures valuation relative to peers in the same sector instead of using one absolute cutoff for all industries.',
          '它衡量的是相对于同行业公司的估值高低，而不是用一个绝对阈值套所有行业。'
        ),
        interpretation: copy(
          language,
          'Lower relative valuation is treated as more attractive. Higher relative valuation is treated as more expensive.',
          '相对行业越便宜，模型越偏正面；相对行业越贵，模型越偏负面。'
        ),
        current: copy(
          language,
          `The raw ratio is ${decimal(signal.value, locale, signal.name === 'pb_percentile' ? 1 : 2)} and the sector-relative score is ${score(signal.score)}.`,
          `当前原始倍数为 ${decimal(signal.value, locale, signal.name === 'pb_percentile' ? 1 : 2)}，行业相对评分为 ${score(signal.score)}。`
        ),
      }
    case 'peg':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'PEG uses the company’s valuation divided by earnings growth expectations. In the long-term model, PEG below 1 scores +2, below 2 scores +1, below 3 scores -1, and above 3 scores -2.',
          'PEG 是估值和利润增长预期的比值。在长期模型里，PEG 低于 1 记 +2，低于 2 记 +1，低于 3 记 -1，超过 3 记 -2。'
        ),
        meaning: copy(
          language,
          'It asks whether valuation is justified by expected growth.',
          '它衡量估值是否被增长预期支撑。'
        ),
        interpretation: copy(
          language,
          'Lower PEG is better as long as growth assumptions are credible. Negative PEG is treated unfavorably because it usually implies negative growth.',
          '只要增长假设可信，PEG 越低越好。PEG 为负通常意味着增长为负，因此会被视为不利。'
        ),
        current: copy(
          language,
          `Current PEG is ${decimal(signal.value, locale, 2)}, giving a long-term score of ${score(signal.score)}.`,
          `当前 PEG 为 ${decimal(signal.value, locale, 2)}，长期评分为 ${score(signal.score)}。`
        ),
      }
    case 'revenue_growth_qoq':
    case 'earnings_growth_qoq':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'This long-term signal uses the latest quarter’s year-over-year growth rate from fundamentals, then scores it with the model’s growth buckets.',
          '这个长期信号使用基本面里的最新季度同比增速，再按模型设定的增长分档打分。'
        ),
        meaning: copy(
          language,
          'It measures whether top-line or bottom-line growth is strong enough to support a long-term thesis.',
          '它衡量营收或利润增长是否足够支撑长期逻辑。'
        ),
        interpretation: copy(
          language,
          'Growth above 15% scores +2, above 5% scores +1, small positive growth is neutral, and negative growth turns bearish.',
          '增速高于 15% 记 +2，高于 5% 记 +1，小幅正增长记中性，负增长则转为空头。'
        ),
        current: copy(
          language,
          `Current growth is ${percent(signal.value, locale)}, so the long-term rule score is ${score(signal.score)}.`,
          `当前增速为 ${percent(signal.value, locale)}，因此长期规则评分为 ${score(signal.score)}。`
        ),
      }
    case 'roe_trend':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'This uses ROE from the latest fundamentals snapshot and scores it with fixed breakpoints: above 20% = +2, above 15% = +1, above 10% = 0, above 5% = -1, else -2.',
          '这个信号使用最新基本面快照里的 ROE，并按固定阈值打分：高于 20% 记 +2，高于 15% 记 +1，高于 10% 记 0，高于 5% 记 -1，否则记 -2。'
        ),
        meaning: copy(
          language,
          'It measures how efficiently equity capital is being used.',
          '它衡量股东权益被使用得是否高效。'
        ),
        interpretation: copy(
          language,
          'Higher ROE is better, but it should still be checked against leverage.',
          'ROE 越高越好，但仍需结合杠杆一起判断。'
        ),
        current: copy(
          language,
          `Current ROE is ${percent(signal.value, locale)}, so the score is ${score(signal.score)}.`,
          `当前 ROE 为 ${percent(signal.value, locale)}，因此评分为 ${score(signal.score)}。`
        ),
      }
    case 'roic_trend':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'ROIC is approximated as net income divided by invested capital, where invested capital = total assets minus current liabilities. The model compares the latest value with the prior period when available.',
          'ROIC 近似按“净利润 ÷ 投入资本”计算，其中投入资本 = 总资产 - 流动负债。若有可用数据，模型还会把最新值和上一期比较。'
        ),
        meaning: copy(
          language,
          'It measures how efficiently the business converts invested capital into profit.',
          '它衡量公司把投入资本转化为利润的效率。'
        ),
        interpretation: copy(
          language,
          'High and improving ROIC is strongest. Weak or negative ROIC is bearish because capital is not compounding well.',
          'ROIC 高且在改善时最强；ROIC 弱甚至为负，则说明资本使用效率较差，会偏空。'
        ),
        current: copy(
          language,
          `Current ROIC is ${percent(signal.value, locale)} and the rule score is ${score(signal.score)}.`,
          `当前 ROIC 为 ${percent(signal.value, locale)}，规则评分为 ${score(signal.score)}。`
        ),
      }
    case 'profitability_margin':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'The long-term model prefers FCF margin = free cash flow / revenue when both numbers exist. If not, it falls back to profit margin with a lower weight.',
          '长期模型优先使用 FCF 利润率 = 自由现金流 ÷ 营收；如果这两个数拿不到，就退回使用净利润率，而且权重更低。'
        ),
        meaning: copy(
          language,
          'It measures the quality of profits and how much economic value the business keeps from each dollar of revenue.',
          '它衡量盈利质量，以及公司每 1 美元营收最终能留下多少经济价值。'
        ),
        interpretation: copy(
          language,
          'Margins above 20% score +2, above 10% score +1, small positive margins are neutral, and negative margins are clearly bearish.',
          '利润率高于 20% 记 +2，高于 10% 记 +1，小幅为正记中性，负利润率则明显偏空。'
        ),
        current: copy(
          language,
          `Current profitability margin is ${percent(signal.value, locale)}, which maps to score ${score(signal.score)}.`,
          `当前盈利能力利润率为 ${percent(signal.value, locale)}，对应评分 ${score(signal.score)}。`
        ),
      }
    case 'debt_equity_trend':
      if (signal.value == null) return null
      return {
        calculation: copy(
          language,
          'This long-term signal uses yfinance debt-to-equity and scores it with thresholds tailored to yfinance’s percentage-style format: below 50 = +2, below 100 = +1, below 200 = -1, above 200 = -2.',
          '这个长期信号使用 yfinance 的负债权益比，并按 yfinance 的百分比口径打分：低于 50 记 +2，低于 100 记 +1，低于 200 记 -1，高于 200 记 -2。'
        ),
        meaning: copy(
          language,
          'It measures balance-sheet leverage and refinancing risk.',
          '它衡量资产负债表杠杆和再融资风险。'
        ),
        interpretation: copy(
          language,
          'Lower leverage is preferred. Higher leverage can amplify returns, but also increases fragility.',
          '模型更偏好低杠杆。高杠杆虽然可能放大回报，但也会提高脆弱性。'
        ),
        current: copy(
          language,
          `Current debt/equity reading is ${decimal(signal.value, locale, 0)} in yfinance format, so the score is ${score(signal.score)}.`,
          `当前负债权益比读数为 ${decimal(signal.value, locale, 0)}（yfinance 口径），因此评分为 ${score(signal.score)}。`
        ),
      }
    case 'yield_curve':
      return {
        calculation: copy(
          language,
          'This macro signal scores the 10Y-2Y Treasury spread. Deep inversion scores -2, mild inversion -1, flat curve 0, normal steepness +1, and very steep curve +2.',
          '这个宏观信号对 10 年期和 2 年期美债利差打分。深度倒挂记 -2，轻度倒挂记 -1，平坦记 0，正常陡峭记 +1，非常陡峭记 +2。'
        ),
        meaning: copy(
          language,
          'It is a broad economic-regime signal: inverted curves often warn about slowdown risk, while steeper curves are more expansionary.',
          '它是一个宏观经济阶段信号：收益率曲线倒挂通常预示放缓风险，曲线更陡则更偏扩张。'
        ),
        interpretation: copy(
          language,
          'Higher scores are macro-supportive for long-duration risk assets; lower scores are macro headwinds.',
          '分数越高，宏观环境越偏支持风险资产；分数越低，宏观阻力越大。'
        ),
        current: copy(
          language,
          `Current yield-curve macro score is ${score(signal.score)}.`,
          `当前收益率曲线宏观评分为 ${score(signal.score)}。`
        ),
      }
    case 'fed_cycle':
      return {
        calculation: copy(
          language,
          'This macro signal looks at the change in Fed funds rate over the last 6 months. Aggressive cuts score +2, mild cuts +1, pauses 0, hikes -1, aggressive hikes -2.',
          '这个宏观信号观察过去 6 个月联邦基金利率的变化。大幅降息记 +2，温和降息记 +1，暂停记 0，加息记 -1，大幅加息记 -2。'
        ),
        meaning: copy(
          language,
          'It captures whether monetary policy is easing or tightening.',
          '它反映货币政策是在宽松还是收紧。'
        ),
        interpretation: copy(
          language,
          'Higher scores mean policy is becoming easier, which is generally supportive for longer-term equity risk. Lower scores mean tighter financial conditions.',
          '分数越高说明政策更趋宽松，通常更支持长期权益风险偏好；分数越低则说明金融条件更紧。'
        ),
        current: copy(
          language,
          `Current Fed-cycle macro score is ${score(signal.score)}.`,
          `当前联储周期宏观评分为 ${score(signal.score)}。`
        ),
      }
    case 'cpi_trend':
      return {
        calculation: copy(
          language,
          'This macro signal combines current CPI year-over-year inflation with its 3-month trend. Low and falling inflation scores highest; high or rising inflation scores lowest.',
          '这个宏观信号会结合当前 CPI 同比通胀水平和最近 3 个月趋势。通胀低且继续回落时评分最高；通胀高或继续上行时评分最低。'
        ),
        meaning: copy(
          language,
          'It measures inflation pressure and whether it is becoming easier or harder for valuations to expand.',
          '它衡量通胀压力，以及估值环境是在改善还是在恶化。'
        ),
        interpretation: copy(
          language,
          'Higher scores mean inflation is under better control. Lower scores mean inflation is more likely to pressure rates and valuations.',
          '分数越高表示通胀控制得更好；分数越低表示通胀更可能继续压制利率和估值。'
        ),
        current: copy(
          language,
          `Current CPI-trend macro score is ${score(signal.score)}.`,
          `当前 CPI 趋势宏观评分为 ${score(signal.score)}。`
        ),
      }
    case 'structural_news':
      return {
        calculation: copy(
          language,
          'The backend scans headlines from the last 30 days for structural keywords such as antitrust, layoffs, lawsuits, approvals, or patents. It averages the matched keyword scores, rounds the result, and clamps it to -2..+2.',
          '后端会扫描最近 30 天新闻标题中的结构性关键词，比如反垄断、裁员、诉讼、审批通过、专利等。匹配到的关键词分数会先取平均，再四舍五入并限制在 -2 到 +2。'
        ),
        meaning: copy(
          language,
          'It tries to capture non-price, non-fundamental events that can change the long-term narrative.',
          '它尝试捕捉那些不直接体现在价格或财报里、但会改变长期叙事的事件。'
        ),
        interpretation: copy(
          language,
          'Higher scores mean the recent structural event mix is favorable. Lower scores mean the recent event mix adds long-term risk.',
          '分数越高说明近期结构性事件更偏正面；分数越低说明近期事件对长期逻辑的风险更大。'
        ),
        current: signal.value == null
          ? null
          : copy(
              language,
              `The model detected ${integer(signal.value, locale)} structural event(s) and assigned score ${score(signal.score)}.`,
              `模型检测到 ${integer(signal.value, locale)} 个结构性事件，并给出 ${score(signal.score)} 分。`
            ),
      }
    default:
      return null
  }
}
