"""Prompt templates for LLM-based stock analysis."""

from __future__ import annotations

from typing import Literal

Language = Literal["zh", "en"]

SYSTEM_PROMPT_ZH = """\
你是一位资深美股分析师，拥有20年的华尔街交易和研究经验。你的分析以数据驱动、逻辑严密著称。

你将收到一只股票的完整量化分析数据，包括：技术指标、基本面指标、宏观经济数据、新闻动态、以及系统评分。

请基于这些数据，用中文给出深入、专业的分析报告，包含以下部分：

## 1. 总体判断
一句话结论 + 信心等级（高/中/低）

## 2. 短期展望（1-2周）
基于技术面信号，明确看涨/看跌/震荡，给出：
- 关键支撑位和阻力位（必须直接引用下方"支撑/阻力结构"中的价位、强度和构成依据，例如"28.50 是强支撑，由 MA60 + POC + 2 次放量 swing low 共振而成"；不要自己另外编造价位）
- 成交量分析
- 动量判断

## 3. 中期展望（1-6个月）
结合趋势、财报动量、板块轮动：
- 趋势方向和强度
- 财报/业绩催化剂
- 相对强度分析

## 4. 长期展望（1-3年）
基于估值、成长性、宏观环境：
- 估值是否合理
- 成长空间和护城河
- 宏观环境影响

## 5. 期权市场隐含信息（如果提供了"期权市场隐含信息"数据）
**必须**严格基于下方"期权市场隐含信息"中的实际数据作答；如未提供则跳过本节。内容包括：
- **期权市场预期的价格区间**：直接引用最近到期的 1σ / 2σ 区间价格（例如"最近到期(YYYY-MM-DD, XX DTE) 期权隐含 1σ 区间 [$A, $B]，约 ±X%；2σ 区间 [$C, $D]"）
- **多空情绪**：基于 Put/Call Ratio（成交量与未平仓）、IV Skew 给出判断（恐慌/平衡/贪婪），并引用具体数值
- **IV Rank（HV 代理）**：说明当前隐含波动率相对历史实现波动率的偏贵/偏便宜
- **关键价位**：引用 Max Pain 与 OI 支撑/阻力簇的具体 strike，说明其作为磁吸/压力位的含义
- 本节是独立的"市场隐含视角"，**不要**把这里的数字再塞回上面的短期关键位

## 6. 风险提示
列出最大的3个风险因素，按影响程度排序

## 7. 潜在催化剂
列出可能推动股价的正面事件

## 8. 操作建议
具体到仓位建议（轻仓/标准/重仓）和进场时机

**重要要求：**
- 每个判断必须引用具体的数据支撑（如"RSI 72处于超买区间"）
- 如果信号之间矛盾，明确指出并解释如何权衡
- 不要模棱两可，给出明确方向判断
- 用 Markdown 格式输出
"""

SYSTEM_PROMPT_EN = """\
You are a senior U.S. equity analyst with 20 years of Wall Street trading and research experience. Your analysis is known for being data-driven and logically rigorous.

You will receive a complete quantitative analysis dataset for a stock, including: technical indicators, fundamental metrics, macroeconomic data, news flow, and system scores.

Based on this data, produce an in-depth, professional analysis report in English with the following sections:

## 1. Overall Judgment
One-sentence conclusion + confidence level (High / Medium / Low)

## 2. Short-Term Outlook (1-2 weeks)
Based on technical signals, clearly state Bullish / Bearish / Range-bound, and provide:
- Key support and resistance levels (you MUST directly cite the price, strength, and composition from the "Support/Resistance Structure" section below — e.g., "28.50 is strong support, formed by MA60 + POC + 2 high-volume swing lows in confluence". Do NOT invent your own levels.)
- Volume analysis
- Momentum assessment

## 3. Medium-Term Outlook (1-6 months)
Combine trend, earnings momentum, and sector rotation:
- Trend direction and strength
- Earnings / results catalysts
- Relative strength analysis

## 4. Long-Term Outlook (1-3 years)
Based on valuation, growth, and the macro environment:
- Whether the valuation is reasonable
- Growth runway and moat
- Macro environment impact

## 5. Options-Implied Outlook (only if "Options-Implied Outlook" data is provided)
You MUST ground this section strictly in the actual values from the "Options-Implied Outlook" block below; skip the section entirely when that block is absent. Cover:
- **Implied price range**: directly cite the nearest-expiry 1σ / 2σ ranges (e.g., "Nearest expiry YYYY-MM-DD (XX DTE) implies a 1σ range of $A–$B (~±X%), 2σ range $C–$D").
- **Sentiment**: interpret Put/Call Ratio (volume and open interest) and IV Skew as fear / balanced / greed, quoting the actual numbers.
- **IV Rank (HV proxy)**: state whether implied vol is rich or cheap versus the 52-week realized-vol distribution.
- **Key strikes**: cite Max Pain and the top open-interest support/resistance strikes, explaining each as a magnet or barrier.
- This section represents the independent "market-implied view" — do NOT recycle these numbers into the Short-Term levels section above.

## 6. Risk Factors
List the top 3 risks, ranked by impact

## 7. Potential Catalysts
List positive events that could drive the stock higher

## 8. Actionable Recommendation
Specify position sizing (light / standard / heavy) and entry timing

**Important requirements:**
- Every judgment must cite specific data support (e.g., "RSI 72 indicates overbought territory")
- If signals conflict, explicitly point this out and explain how you weigh them
- Do not be ambiguous — give a clear directional call
- Output in Markdown format
"""


def get_system_prompt(language: Language = "zh") -> str:
    return SYSTEM_PROMPT_EN if language == "en" else SYSTEM_PROMPT_ZH


# Backwards-compatible alias
SYSTEM_PROMPT = SYSTEM_PROMPT_ZH


_LABELS = {
    "zh": {
        "stock": "股票",
        "company": "公司",
        "price": "当前价格",
        "change": "日涨跌幅",
        "score_suffix": "评分",
        "rule_score": "规则评分",
        "verdict": "判定",
        "confidence": "置信度",
        "signals": "信号明细",
        "levels_header": "支撑/阻力结构（已按成交量、时间衰减、多源共振综合评分，strength 越大越强）:",
        "distance": "距现价",
        "basis": "依据",
        "news": "近期新闻",
        "sentiment": "情绪",
        "risks": "已识别风险",
        "caveats": "数据注意事项",
        "options_header": "期权市场隐含信息",
        "options_source": "数据来源",
        "implied_ranges": "隐含价格区间（按到期日）",
        "expiry": "到期",
        "dte": "剩余天数",
        "atm_iv": "ATM IV",
        "expected_move": "隐含波动幅度",
        "straddle": "跨式报价",
        "range_1s": "1σ 区间",
        "range_2s": "2σ 区间",
        "iv_rank_label": "IV Rank（HV 代理）",
        "pcr_vol_label": "成交量 Put/Call 比",
        "pcr_oi_label": "未平仓 Put/Call 比",
        "iv_skew_label": "IV Skew（25Δ Put − Call）",
        "max_pain_label": "Max Pain 价位",
        "oi_support": "OI 支撑簇（高 put OI）",
        "oi_resistance": "OI 阻力簇（高 call OI）",
        "options_summary": "一句话要点",
    },
    "en": {
        "stock": "Stock",
        "company": "Company",
        "price": "Current Price",
        "change": "Daily Change",
        "score_suffix": "Score",
        "rule_score": "Rule Score",
        "verdict": "Verdict",
        "confidence": "Confidence",
        "signals": "Signal Details",
        "levels_header": "Support/Resistance Structure (scored by volume, time decay, and multi-source confluence; higher strength = stronger level):",
        "distance": "distance from current",
        "basis": "basis",
        "news": "Recent News",
        "sentiment": "sentiment",
        "risks": "Identified Risks",
        "caveats": "Data Caveats",
        "options_header": "Options-Implied Outlook",
        "options_source": "Data source",
        "implied_ranges": "Implied Price Ranges (by expiry)",
        "expiry": "Expiry",
        "dte": "DTE",
        "atm_iv": "ATM IV",
        "expected_move": "Expected move",
        "straddle": "Straddle",
        "range_1s": "1σ range",
        "range_2s": "2σ range",
        "iv_rank_label": "IV Rank (HV proxy)",
        "pcr_vol_label": "Volume Put/Call Ratio",
        "pcr_oi_label": "Open-Interest Put/Call Ratio",
        "iv_skew_label": "IV Skew (25Δ Put − Call)",
        "max_pain_label": "Max Pain strike",
        "oi_support": "OI Support clusters (high put OI)",
        "oi_resistance": "OI Resistance clusters (high call OI)",
        "options_summary": "Summary",
    },
}


def build_user_prompt(report_data: dict, language: Language = "zh") -> str:
    """Build the user prompt with all analysis data as structured JSON."""
    import json

    L = _LABELS["en" if language == "en" else "zh"]
    sections = []

    sections.append(f"## {L['stock']}: {report_data.get('ticker', 'N/A')}")
    sections.append(f"{L['company']}: {report_data.get('company_name', 'N/A')}")
    if report_data.get("as_of_price"):
        sections.append(f"{L['price']}: ${report_data['as_of_price']:.2f}")
    if report_data.get("price_change_pct"):
        sections.append(f"{L['change']}: {report_data['price_change_pct']:+.2%}")

    for horizon_key in ["short_term", "medium_term", "long_term"]:
        h = report_data.get(horizon_key)
        if h:
            sections.append(f"\n## {horizon_key} {L['score_suffix']}")
            sections.append(f"{L['rule_score']}: {h.get('rule_score', 'N/A')}/100")
            sections.append(f"{L['verdict']}: {h.get('verdict', 'N/A')}")
            sections.append(f"{L['confidence']}: {h.get('confidence', 'N/A')}")
            if h.get("signals"):
                sections.append(f"{L['signals']}:")
                sections.append("```json")
                sections.append(json.dumps(h["signals"], ensure_ascii=False, indent=2, default=str))
                sections.append("```")
            levels = h.get("levels") or []
            if levels:
                sections.append(L["levels_header"])
                for lv in levels:
                    sources = lv.get("sources") or []
                    src_txt = ", ".join(
                        f"{s.get('kind')}@{s.get('price')}" for s in sources[:6]
                    )
                    sections.append(
                        f"- [{lv.get('kind')}] ${lv.get('price')}  "
                        f"strength={lv.get('strength')}  "
                        f"{L['distance']} {float(lv.get('distance_pct', 0)) * 100:+.2f}%  "
                        f"{L['basis']}: {src_txt}"
                    )

    news = report_data.get("news", [])
    if news:
        sections.append(f"\n## {L['news']}")
        for n in news[:10]:
            sent = n.get("sentiment", 0)
            emoji = "📈" if sent > 0.2 else "📉" if sent < -0.2 else "📰"
            sections.append(
                f"- {emoji} [{n.get('source', '')}] {n.get('headline', '')} "
                f"({L['sentiment']}: {sent:+.2f})"
            )

    options = report_data.get("options_outlook")
    if options:
        sections.append(f"\n## {L['options_header']}")
        src = options.get("data_source") or "N/A"
        spot = options.get("spot")
        spot_txt = f"${spot:.2f}" if isinstance(spot, (int, float)) else "N/A"
        sections.append(f"{L['options_source']}: {src}  |  Spot: {spot_txt}")

        if options.get("summary"):
            sections.append(f"{L['options_summary']}: {options['summary']}")

        ranges = options.get("implied_ranges") or []
        if ranges:
            sections.append(f"\n### {L['implied_ranges']}")
            for r in ranges:
                parts = [
                    f"{L['expiry']}={r.get('expiry')}",
                    f"{L['dte']}={r.get('dte')}",
                ]
                if r.get("atm_iv") is not None:
                    parts.append(f"{L['atm_iv']}={r['atm_iv']:.2%}")
                if r.get("expected_move_pct") is not None:
                    parts.append(f"{L['expected_move']}=±{r['expected_move_pct']:.2%}")
                if r.get("straddle_price") is not None:
                    parts.append(f"{L['straddle']}=${r['straddle_price']:.2f}")
                if r.get("range_1sigma_low") is not None and r.get("range_1sigma_high") is not None:
                    parts.append(
                        f"{L['range_1s']}=[${r['range_1sigma_low']:.2f}, ${r['range_1sigma_high']:.2f}]"
                    )
                if r.get("range_2sigma_low") is not None and r.get("range_2sigma_high") is not None:
                    parts.append(
                        f"{L['range_2s']}=[${r['range_2sigma_low']:.2f}, ${r['range_2sigma_high']:.2f}]"
                    )
                sections.append("- " + "  |  ".join(parts))

        def _metric_line(label_key: str, metric: dict | None) -> None:
            if not metric:
                return
            val = metric.get("value")
            val_txt = f"{val:.4f}" if isinstance(val, (int, float)) else "N/A"
            rationale = metric.get("rationale", "")
            sections.append(f"- **{L[label_key]}**: {val_txt} — {rationale}")

        sections.append("")
        _metric_line("iv_rank_label", options.get("iv_rank"))
        _metric_line("pcr_vol_label", options.get("pcr_volume"))
        _metric_line("pcr_oi_label", options.get("pcr_oi"))
        _metric_line("iv_skew_label", options.get("iv_skew"))
        _metric_line("max_pain_label", options.get("max_pain"))

        def _render_oi(label_key: str, strikes: list[dict]) -> None:
            if not strikes:
                return
            sections.append(f"\n### {L[label_key]}")
            for s in strikes:
                sections.append(
                    f"- strike ${s.get('strike'):.2f}  "
                    f"call OI={s.get('call_oi', 0)}  put OI={s.get('put_oi', 0)}  "
                    f"{L['distance']} {float(s.get('distance_pct', 0)) * 100:+.2f}%"
                )

        _render_oi("oi_support", options.get("oi_support") or [])
        _render_oi("oi_resistance", options.get("oi_resistance") or [])

    risks = report_data.get("risks", [])
    if risks:
        sections.append(f"\n## {L['risks']}")
        for r in risks:
            sections.append(f"- {r}")

    caveats = report_data.get("caveats", [])
    if caveats:
        sections.append(f"\n## {L['caveats']}")
        for c in caveats:
            sections.append(f"- {c}")

    return "\n".join(sections)
