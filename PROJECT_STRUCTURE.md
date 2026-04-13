# 项目结构说明

## 1. 项目定位

这是一个“多周期美股分析平台”，后端使用 Python 实现分析流水线和 API，前端使用 React + Vite 展示分析结果。

项目支持两种主要使用方式：

- 命令行模式：通过 `stockpredict analyze` 或 `python -m stockpredict` 运行分析。
- Web 模式：通过 FastAPI 提供 `/api/*` 接口，并在生产环境下直接托管 `frontend/dist` 静态页面。

核心能力集中在 `src/stockpredict` 包中，围绕“数据抓取 -> 指标计算 -> 多周期评分 -> AI 解读 -> 结果持久化/展示”展开。

## 2. 顶层目录

```text
stock-predict/
├── Pipfile
├── Pipfile.lock
├── pyproject.toml
├── .env.example
├── config/
├── src/
│   └── stockpredict/
├── frontend/
├── scripts/
├── tests/
├── cache/
├── data/
├── models/
└── reports/
```

各目录职责如下：

- `Pipfile`：`pipenv` 环境入口，安装项目本体和开发依赖。
- `Pipfile.lock`：`pipenv` 锁文件，固定当前解析出的依赖版本。
- `pyproject.toml`：Python 项目入口，定义依赖、构建方式和 CLI 命令 `stockpredict`。
- `config/`：运行配置与权重配置。
- `src/stockpredict/`：后端主代码目录，也是项目的核心包。
- `frontend/`：React 前端工程，负责发起分析请求、订阅进度、展示报告。
- `scripts/`：独立脚本，包含一键启动前后端的开发脚本和 IBKR 连通性烟雾测试。
- `tests/`：测试目录，目前为空，尚未看到自动化测试实现。
- `cache/`：磁盘缓存目录，运行时写入行情、基本面、宏观等缓存文件。
- `data/`：SQLite 数据库默认所在目录，当前目录存在但内容为空。
- `models/`：为机器学习模型预留的目录，当前为空。
- `reports/`：CLI 导出的 JSON 分析报告默认输出目录，当前为空。

## 3. 后端代码结构

`src/stockpredict` 的主要结构如下：

```text
src/stockpredict/
├── __main__.py
├── cli.py
├── pipeline.py
├── types.py
├── analysis/
├── indicators/
├── strategy/
├── ml/
├── ai/
├── data/
├── db/
├── api/
└── templates/
```

### 3.1 入口层

- `__main__.py`
  允许通过 `python -m stockpredict` 启动项目，本质上转发到 CLI。
- `cli.py`
  命令行入口，基于 Typer 提供两个命令：
  - `analyze`：对一个或多个 ticker 执行分析，并把结果输出到终端和 `reports/`。
  - `serve`：启动 Uvicorn，加载 FastAPI 应用。
- `pipeline.py`
  项目主流程编排器，是最核心的后端文件。

### 3.2 核心领域模型

- `types.py`
  定义项目共享的数据模型，主要包括：
  - `Horizon`：`short_term` / `medium_term` / `long_term`
  - `Verdict`：`Strong Buy` 到 `Strong Sell`
  - `Signal`：单个指标信号
  - `HorizonScore`：单周期汇总结果
  - `NewsItem`：新闻项
  - `Report`：完整分析报告
  - `ProgressUpdate`：进度推送结构

这说明整个项目是“先生成结构化 `Report`，再给 CLI、API、前端、AI 统一消费”的设计。

## 4. 分析流水线

`src/stockpredict/pipeline.py` 负责串联全部分析步骤。当前流程如下：

1. 读取 `config/settings.py` 和 `config/weights.yaml`。
2. 初始化磁盘缓存 `DiskCache`。
3. 获取价格数据：
   - 优先用 `IBKRClient`
   - 否则回退到 `YFinanceClient`
4. 获取基本面数据（yfinance）。
5. 获取新闻数据（Finnhub，可选）。
6. 获取宏观数据（FRED，可选）。
7. 获取基准指数 `SPY` 数据，用于相对强弱比较。
8. 构造 `AnalysisContext`。
9. 依次执行三个分析器：
   - `ShortTermAnalyzer`
   - `MediumTermAnalyzer`
   - `LongTermAnalyzer`
10. 对每个周期调用 `score_horizon` 计算规则分。
11. 调用 `aggregate` 将规则分与 ML 概率合并。
12. 如果 AI 开启，则调用 LLM 生成中文 Markdown 总结。
13. 组装 `Report` 并返回。

项目的总体控制流很集中，没有把流程拆成很多服务，属于典型的单体式分析应用。

## 5. 分析层和指标层

### 5.1 `analysis/`：按投资周期组织

- `base.py`
  定义 `AnalysisContext` 和抽象基类 `HorizonAnalyzer`。
- `short_term.py`
  关注短期技术面和短期新闻情绪，主要使用：
  - MA 交叉
  - RSI
  - MACD
  - 布林带
  - ATR 波动状态
  - OBV
  - 成交量放大
  - 5 日动量分位
  - 24 小时新闻情绪
- `medium_term.py`
  关注趋势和中期基本面动量，主要使用：
  - MA50/MA200
  - 价格相对 MA200 偏离
  - 52 周位置
  - 相对 SPY 强弱
  - 营收增长
  - 盈利增长
  - 波动率 regime 变化
- `long_term.py`
  关注估值、质量、成长和宏观环境，主要使用：
  - P/E、P/B、PEG、EV/EBITDA
  - 营收/盈利增长
  - ROE、利润率、债务水平
  - 收益率曲线、加息周期、CPI 趋势
  - 结构性新闻事件

这层的设计重点是：不同周期使用不同信号组合，而不是一套指标硬套所有周期。

### 5.2 `indicators/`：纯计算函数层

- `technical.py`：技术指标和趋势函数，如 `sma`、`rsi`、`macd`、`atr`、`relative_strength`。
- `fundamental.py`：估值/财务质量打分函数，如 `peg_score`、`roe_score`、`debt_equity_score`。
- `macro.py`：宏观序列状态判断，如收益率曲线、联储周期、CPI 趋势。
- `news.py`：新闻情绪汇总、新闻量 z-score、结构性事件抽取。

这层基本是“无状态函数库”，供 `analysis/` 调用。

## 6. 评分与模型层

### 6.1 `strategy/`

- `scoring.py`
  把多个 `Signal` 归一化为 `[-100, 100]` 的周期评分，并生成 `Verdict` 与 `confidence`。
- `aggregator.py`
  用规则分和 ML 概率做加权合并。

当前评分逻辑是：

- 规则信号先加权求和。
- ML 输出的是“上涨概率”。
- 当 ML 输出为 `0.5` 时，等价于没有提供额外信息。

### 6.2 `ml/`

- `predictor.py`
  目前只有占位实现 `NaiveBaselinePredictor`。

这说明项目已经为 ML 留了扩展口，但当前实际运行仍以规则引擎为主，ML 只是占位。

## 7. 数据接入层

`data/` 是所有外部数据源的适配层：

- `cache.py`
  文件缓存实现，支持 parquet 和 json，两者都带 TTL。
- `ibkr_client.py`
  对 Interactive Brokers Gateway 的异步封装，可取历史 K 线、快照报价、合约信息。
- `yfinance_client.py`
  免费数据备份来源，提供价格历史、基本面、财务报表、分析师推荐等。
- `fred_client.py`
  拉取 FRED 宏观序列。
- `finnhub_client.py`
  拉取公司新闻。

项目的数据源策略很明确：

- 价格数据优先 IBKR，失败后回退 yfinance。
- 基本面主要来自 yfinance。
- 新闻依赖 Finnhub API Key。
- 宏观依赖 FRED API Key。

## 8. AI 层

`ai/` 负责在结构化报告之上追加自然语言分析：

- `prompts.py`
  定义中文系统提示词，并把结构化 `Report` 转成用户提示。
- `providers.py`
  封装 OpenAI 和 Claude 两种 LLM Provider。
- `analyzer.py`
  统一执行 AI 分析，输出 Markdown 字符串。

这一层和量化分析是解耦的：前面先产出 `Report`，AI 只是对结果做二次解释。

## 9. 持久化与 API 层

### 9.1 `db/`

- `models.py`
  定义 `Analysis` ORM 模型，对每次分析做持久化。
- `database.py`
  初始化 SQLite 异步引擎与 session factory。
- `crud.py`
  提供保存、更新、按 ticker 查询历史、查询最近分析等操作。

数据库设计采用“列表字段反规范化 + 完整报告 JSON 存 blob”的组合：

- 列表页常用字段（ticker、score、verdict）单独存列，便于快速查询。
- 完整 `Report` 以 JSON 字符串存进 `report_json`，便于详情页直接回放。

### 9.2 `api/`

- `app.py`
  创建 FastAPI 应用，注册路由，初始化数据库，并在存在 `frontend/dist` 时托管静态页面。
- `deps.py`
  提供数据库 session 和 settings 依赖。
- `routes/analyze.py`
  发起后台分析任务，支持 24 小时缓存命中。
- `routes/status.py`
  通过 SSE 推送分析进度。
- `routes/detail.py`
  查询单次分析详情。
- `routes/history.py`
  查询某个 ticker 的历史分析和全局最近分析。

当前 Web 交互模型是：

- 先 `POST /api/analyze/{ticker}`
- 再订阅 `GET /api/status/{task_id}`
- 完成后请求 `GET /api/analysis/{id}`

这是一个很典型的“异步后台任务 + SSE 进度”模式。

## 10. 前端结构

`frontend/` 是一个独立的 Vite + React + TypeScript 应用。

```text
frontend/
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/client.ts
│   ├── components/
│   ├── styles/globals.css
│   ├── types/index.ts
│   └── hooks/
└── dist/              # 构建产物
```

### 10.1 页面和路由

- `src/main.tsx`
  挂载 `BrowserRouter`。
- `src/App.tsx`
  只有两个页面路由：
  - `/` -> `HomePage`
  - `/analyze/:ticker` -> `AnalyzePage`

### 10.2 API 访问层

- `src/api/client.ts`
  封装后端调用：
  - `startAnalysis`
  - `getAnalysisDetail`
  - `getHistory`
  - `getRecent`
  - `subscribeToProgress`

### 10.3 组件职责

- `HomePage.tsx`
  首页，提供 ticker 输入框和最近分析列表。
- `AnalyzePage.tsx`
  分析结果页，负责启动分析、监听 SSE、加载最终报告、导出 JSON。
- `Dashboard.tsx`
  结果总览页容器。
- `ScoreCard.tsx`
  展示短中长期评分卡。
- `PriceChart.tsx`
  展示价格图表。
- `AIAnalysis.tsx`
  展示 AI 生成的 Markdown 总结。
- `SignalTable.tsx`
  展示每个周期的信号明细。
- `NewsPanel.tsx`
  展示新闻列表。
- `HistoryList.tsx`
  展示同一 ticker 的历史分析。
- `ProgressBar.tsx`
  展示后台任务进度。
- `TickerInput.tsx`
  输入股票代码。

### 10.4 类型同步

- `frontend/src/types/index.ts`
  基本镜像了后端 `types.py` 的结构，说明前后端通信依赖统一的数据形状。

## 11. 配置与环境

### 11.1 `config/settings.py`

集中管理以下配置：

- IBKR 连接参数
- AI Provider 与模型选择
- ML 权重与模型目录
- API Key（FRED、Finnhub）
- SQLite 路径
- 缓存目录、报告目录、权重文件路径

配置来源是 `.env`，类型校验由 Pydantic Settings 完成。

### 11.2 `Pipfile` / `Pipfile.lock`

项目现在使用 `pipenv` 管理 Python 开发环境：

- `Pipfile` 通过 `editable` 方式安装当前项目。
- 运行时依赖仍然以 `pyproject.toml` 为包元数据来源。
- 开发依赖和常用脚本由 `pipenv` 统一管理。

### 11.3 `config/weights.yaml`

定义短、中、长期信号的权重，是规则评分的核心配置文件之一。

特点：

- 可直接调权重，不需要改代码。
- 目前有一部分权重键已经配置，但分析器中尚未完全使用，说明后续功能有扩展预留。

## 12. 脚本与运行产物

- `scripts/run_project.py`
  并发启动后端 FastAPI 服务和前端 Vite dev server，并统一处理停止信号。
- `scripts/smoke_ibkr.py`
  用于验证 IBKR Gateway 是否可连接，并尝试拉取样例行情。
- `frontend/dist/`
  前端构建产物。
- `frontend/node_modules/`
  前端依赖目录。
- `__pycache__/`
  Python 字节码缓存。

这些都不属于核心源码逻辑。

## 13. 当前项目的结构特点

从结构上看，这个项目有几个明显特征：

- 单体结构清晰：后端、前端、配置、缓存、数据库都在一个仓库内。
- 领域边界明确：数据源、分析器、指标、评分、AI、API、前端拆分合理。
- 数据流统一：所有输出最后都汇总成 `Report`。
- 可扩展性不错：ML、AI Provider、更多信号、更多数据源都留了扩展点。
- 工程化还在早期：测试覆盖仍然不高，`templates/`、`frontend/src/hooks/` 这类扩展位也还没形成稳定结构。

## 14. 一句话总结

这个仓库本质上是一个“以 `pipeline.py` 为中心的多周期股票分析单体应用”：

- 后端负责采集数据、计算指标、生成评分与报告。
- API 负责异步触发与结果查询。
- 前端负责把结构化报告可视化。
- AI 模块负责把量化结果翻译成中文分析结论。
