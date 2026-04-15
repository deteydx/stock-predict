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

## 5. 风险提示
列出最大的3个风险因素，按影响程度排序

## 6. 潜在催化剂
列出可能推动股价的正面事件

## 7. 操作建议
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

## 5. Risk Factors
List the top 3 risks, ranked by impact

## 6. Potential Catalysts
List positive events that could drive the stock higher

## 7. Actionable Recommendation
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
