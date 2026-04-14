"""Prompt templates for LLM-based stock analysis."""

from __future__ import annotations

SYSTEM_PROMPT = """\
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


def build_user_prompt(report_data: dict) -> str:
    """Build the user prompt with all analysis data as structured JSON."""
    import json

    sections = []

    # Ticker and price
    sections.append(f"## 股票: {report_data.get('ticker', 'N/A')}")
    sections.append(f"公司: {report_data.get('company_name', 'N/A')}")
    if report_data.get("as_of_price"):
        sections.append(f"当前价格: ${report_data['as_of_price']:.2f}")
    if report_data.get("price_change_pct"):
        sections.append(f"日涨跌幅: {report_data['price_change_pct']:+.2%}")

    # Horizon scores
    for horizon_key in ["short_term", "medium_term", "long_term"]:
        h = report_data.get(horizon_key)
        if h:
            sections.append(f"\n## {horizon_key} 评分")
            sections.append(f"规则评分: {h.get('rule_score', 'N/A')}/100")
            sections.append(f"判定: {h.get('verdict', 'N/A')}")
            sections.append(f"置信度: {h.get('confidence', 'N/A')}")
            if h.get("signals"):
                sections.append("信号明细:")
                sections.append("```json")
                sections.append(json.dumps(h["signals"], ensure_ascii=False, indent=2, default=str))
                sections.append("```")
            levels = h.get("levels") or []
            if levels:
                sections.append(
                    "支撑/阻力结构（已按成交量、时间衰减、多源共振综合评分，strength 越大越强）:"
                )
                for lv in levels:
                    sources = lv.get("sources") or []
                    src_txt = ", ".join(
                        f"{s.get('kind')}@{s.get('price')}" for s in sources[:6]
                    )
                    sections.append(
                        f"- [{lv.get('kind')}] ${lv.get('price')}  "
                        f"strength={lv.get('strength')}  "
                        f"距现价 {float(lv.get('distance_pct', 0)) * 100:+.2f}%  "
                        f"依据: {src_txt}"
                    )

    # News
    news = report_data.get("news", [])
    if news:
        sections.append("\n## 近期新闻")
        for n in news[:10]:
            sent = n.get("sentiment", 0)
            emoji = "📈" if sent > 0.2 else "📉" if sent < -0.2 else "📰"
            sections.append(
                f"- {emoji} [{n.get('source', '')}] {n.get('headline', '')} "
                f"(情绪: {sent:+.2f})"
            )

    # Risks and caveats
    risks = report_data.get("risks", [])
    if risks:
        sections.append("\n## 已识别风险")
        for r in risks:
            sections.append(f"- {r}")

    caveats = report_data.get("caveats", [])
    if caveats:
        sections.append("\n## 数据注意事项")
        for c in caveats:
            sections.append(f"- {c}")

    return "\n".join(sections)
