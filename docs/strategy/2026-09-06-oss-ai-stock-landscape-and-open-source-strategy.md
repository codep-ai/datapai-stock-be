# OSS AI-Stock Landscape vs DATAP.AI — Leverage Plan + Open-Source Strategy

**Date:** 2026-09-06
**Author:** Donny Zhao (with Claude Code)
**Scope:** competitive scan of the top open-source AI stock/trading repos; gap analysis against `datapai-stock-be`; a ranked "what to steal" plan; and a 2C open-source strategy aimed at stars and forks.

Star/fork numbers below were pulled live from the GitHub API on 2026-09-06, not from blog posts.

---

## 1. The landscape

### 1.1 Leaderboard (verified 2026-09-06)

| Repo | Stars | Forks | License | Last push | What it actually is |
|---|---:|---:|---|---|---|
| `TauricResearch/TradingAgents` | 102,622 | 19,785 | Apache-2.0 | 2026-09-01 | Multi-agent LLM trading-firm simulation |
| `OpenBB-finance/OpenBB` | 72,704 | 7,511 | AGPL-ish (NOASSERTION) | 2026-07-30 | Open data platform / provider abstraction |
| `ZhuLinsen/daily_stock_analysis` | 64,667 | **54,200** | MIT | 2026-09-05 | LLM daily dashboard, runs free on GH Actions |
| `virattt/ai-hedge-fund` | 63,253 | 11,110 | MIT | 2026-09-03 | Investor-persona agents + backtester |
| `freqtrade/freqtrade` | 54,049 | 11,209 | GPL-3.0 | 2026-09-05 | Crypto trading bot |
| `microsoft/qlib` | 48,325 | 7,647 | MIT | 2026-09-02 | Serious quant ML platform (+ RD-Agent) |
| `wilsonfreitas/awesome-quant` | 29,447 | — | none | 2026-09-06 | Curated list |
| `ranaroussi/yfinance` | 25,176 | 3,412 | Apache-2.0 | 2026-08-27 | Free market data |
| `mementum/backtrader` | 23,146 | 5,265 | GPL-3.0 | **2024-08** | Backtester — effectively unmaintained |
| `AI4Finance-Foundation/FinGPT` | 21,210 | 3,010 | MIT | 2026-09-03 | Financial LLM fine-tunes |
| `stefan-jansen/machine-learning-for-trading` | 20,792 | — | MIT | 2026-09-06 | Book companion code |
| `quantopian/zipline` | 20,081 | 5,048 | Apache-2.0 | **2024-02** | Dead |
| `UFund-Me/Qbot` | 18,451 | — | MIT | 2026-03-11 | CN fully-local quant bot |
| `AI4Finance-Foundation/FinRL` | 16,221 | 3,487 | MIT | 2026-07-13 | Financial reinforcement learning |
| `microsoft/RD-Agent` | 14,524 | — | MIT | 2026-09-04 | Automated factor/model R&D |
| `StockSharp/StockSharp` | 10,702 | 2,260 | NOASSERTION | 2026-09-05 | C# algo platform |
| `polakowo/vectorbt` | 9,003 | 1,157 | NOASSERTION | 2026-08-02 | Vectorised backtesting |
| `kernc/backtesting.py` | 8,934 | 1,532 | AGPL-3.0 | 2026-08-05 | Simple backtester |
| `jesse-ai/jesse` | 8,418 | 1,216 | MIT | 2026-09-04 | Crypto bot |
| `AI4Finance-Foundation/FinRobot` | 7,920 | — | Apache-2.0 | 2026-08-23 | Financial agent platform |
| `ranaroussi/quantstats` | 7,617 | — | Apache-2.0 | 2026-07-20 | Portfolio tearsheets |
| `robcarver17/pysystemtrade` | 3,500 | 1,068 | GPL-3.0 | 2026-07-18 | Systematic futures trading |
| `24mlight/A_Share_investment_Agent` | 2,476 | 620 | NOASSERTION | 2026-05-26 | A-share agent |

### 1.2 Cons and cost, per leader

**TradingAgents (102.6k ★, Apache-2.0)**
- *Pros:* the canonical multi-agent architecture (4 analysts → bull/bear researchers → trader → 3 risk roles → PM); reflection + memory; 12+ LLM providers incl. Ollama/Bedrock; HK/TSE/LSE/India/CA/ASX/A-share coverage; token-aware USD budget caps; checkpoint resume.
- *Cons:* research prototype, not a product — no multi-tenancy, no user system, no database of record, file/checkpoint persistence. Explicitly non-deterministic ("two runs of the same ticker and date can differ"). Simulated exchange only, no live broker. No point-in-time data discipline, so any backtest inherits **LLM lookahead** — the model has read the future in its training corpus.
- *Cost:* the worst of the group. One deep run fans out ~10 agent turns per ticker. The dominant cost driver in agentic workflows is turns, not per-token price; with reasoning models at ~$15/$60 per M tokens in/out, a 50-ticker nightly batch is a real monthly bill, not a rounding error.

**ai-hedge-fund (63.3k ★, MIT)**
- *Pros:* cleanest abstraction in the field — investor personas (Buffett, Munger, Burry…) as pluggable, backtestable *alpha models*; backtester with equity curve vs benchmark; mandate files.
- *Cons:* requires a **paid Financial Datasets API** beyond a handful of free tickers; explicitly "educational and research only, not for real trading"; US-centric; local-file persistence; no scheduler, no multi-user, no notification surface.
- *Cost:* LLM + a paid data subscription. Data is the binding constraint, not tokens.

**daily_stock_analysis (64.7k ★ / 54.2k forks, MIT)**
- *Pros:* the growth-hacking champion. **84% fork-to-star ratio because forking IS the install** — fork, add secrets, GH Actions cron runs it free. 5-minute setup. Free data (AkShare/Baostock/yfinance), 6 notification channels (WeCom/Feishu/Telegram/Discord/Slack/email), CN/HK/US/JP/KR/TW.
- *Cons:* thin engine — single-pass LLM summary, not a debate; free data sources throttle and break; no accountability loop (it never scores its own past calls); backtesting is bolted on via a sibling project; MIT means nothing stops a commercial clone.
- *Cost:* genuinely ~$0 infra; LLM cost is one call per ticker per day, or zero with Ollama.

**Qlib (48.3k ★, MIT)**
- *Pros:* the only one with real quant rigour — point-in-time data handling, Alpha158/Alpha360 factor sets, walk-forward evaluation, RL, and RD-Agent for automated factor mining.
- *Cons:* steep learning curve; heavy data-prep burden; not LLM-native (LLM is a bolt-on); no explainability narrative, no product surface, no notifications.
- *Cost:* compute and engineer-hours, not tokens.

**OpenBB (72.7k ★)**
- *Pros:* best-in-class data abstraction — 100+ providers behind one interface, now explicitly positioned "for AI agents".
- *Cons:* it is a data platform, not a strategy. **License is a commercial trap** — the platform is AGPL-family; bundling it into a shipped product creates copyleft obligations. Heavy dependency footprint.

**freqtrade (54.0k ★) / backtesting.py (8.9k ★) / pysystemtrade (3.5k ★)** — GPL-3.0 / AGPL-3.0. Excellent code, **cannot be bundled** into a closed commercial product. Reference only.

**FinRL / FinGPT / FinRobot (AI4Finance)** — strong papers, notebook-heavy, brittle in production, slow-moving. Mine for ideas, don't depend on them.

### 1.3 The one criticism that applies to all of them

**No public repo in this list has demonstrated risk-adjusted alpha out-of-sample.** Every one of them carries an educational-only disclaimer. The LLM-based ones additionally cannot produce an honest backtest, because the model was trained on the outcome. Treat every star count as a measure of *distribution*, not of *edge*.

---

## 2. Where `datapai-stock-be` actually stands

Repo facts: **794 Python files, ~211,500 LOC, 95 commits, 2026-04-03 → 2026-09-04**, private on `codep-ai`.

### 2.1 What we have that the entire top-20 does not

1. **A production data plane.** 17 exchanges (ASX, US, HKEX, SSE, SZSE, TSE, TWSE, SGX, KLSE, SET, IDX, HOSE, HNX, LSE), per-exchange refresh scripts, daily + intraday + weekly + monthly TA, FX rates, index constituents, i18n stock names, EOD reconciliation, S3 → Snowflake → Iceberg archival. Every repo above calls yfinance at request time and has no pipeline.
2. **An accountability loop.** `compute_signal_performance.py` scores 7/30/90-day forward returns vs `^GSPC`; `reflector.py` writes lessons back into `sys_agent_memory` / `sys_agent_results`; `learning_agent.py` and `optimize_signals.py` close the loop. TradingAgents has reflection; nobody else scores their own historical calls against a benchmark in a database.
3. **Trade-level backtests with real metrics.** `backtest_trade_lifecycle.py` compares four strategies (baseline / risk-gated / exit-managed / full-committee) on win rate, profit factor, max drawdown, Sharpe-like ratio and exit-reason breakdown. ai-hedge-fund's backtester is an equity curve.
4. **AI governance and an audit trail.** `guardrail_bridge.py` → `fct_ai_guardrail_decision`, `dim_ai_control` SCD2 point-in-time policy reconstruction, APRA/ASIC/OWASP citations in-session. **Zero** of the 20 repos above has anything comparable. This is the actual moat.
5. **A product surface.** Multi-user, pricing tiers, CRM sync (Twenty), Telegram + Expo push, weekly digest, chat with history + per-user learned context, screener, watchlist, i18n.
6. **Alternative-data agents.** TinyFish IR-page change detection (tone shift, forward guidance, risk disclosure, cross-validation, investigation), ASX announcement agent, SEC filing agent, chart vision. This is closer to real buy-side alt-data than anything in the OSS list.
7. **A broker read-path.** moomoo/Futu OpenD trade history + positions, with a timing analyzer that tells the user they entered three days late.

### 2.2 What the leaders have that we don't

1. **Point-in-time discipline.** `backtest_multi_factor.py` loads *current* `fundamental_lite` rows and applies them to *historical* signal dates. That is textbook lookahead bias. Separately, `compute_signal_performance.py` has a path that generates "realistic sample data clearly marked as simulated" when real signals are sparse — fine for a demo, fatal if a number from it ever reaches a deck or a customer.
2. **Factor breadth.** Qlib ships Alpha158/Alpha360. We have roughly ten TA indicators plus fundamental votes.
3. **RL / automated factor discovery.** FinRL, RD-Agent.
4. **Portfolio construction.** We size individual positions (`risk_agent.py`) but there is no covariance, sector-constraint, vol-target or Kelly layer. cvxpy / quantstats / pysystemtrade all have this.
5. **Determinism and replay.** The debate was cut from 2 rounds to 1 for throughput; there is no pinned seed/temperature/model-version/prompt-hash, so a past decision cannot be re-run identically. For a company selling governance, replayability is table stakes, not a nice-to-have.
6. **Distribution.** 0 stars, private repo, **no README, no LICENSE**.

---

## 3. What to steal — ranked

### P0 — do before publishing any performance number (weeks)

1. **Point-in-time fundamentals** *(source: Qlib)*. Add `datapai.fundamental_lite_history(ticker, exchange, as_of_date, …)`; make every backtest join on `as_of_date <= signal_date`. Until this lands, no backtest output is publishable.
2. **Quarantine the synthetic data path** *(source: ourselves)*. Gate the sample-data generator in `compute_signal_performance.py` behind an explicit `--seed-sample` flag *and* an `is_simulated` column, and exclude simulated rows from every aggregate.
3. **Cost governor on the debate** *(source: TradingAgents)*. They now enforce token-aware USD budget caps. We already have `cost_guard.py` in platform-be and `conflict_meter.py` + `select_synthesis_candidates.py` for triage — wire them into an explicit per-ticker and per-night USD ceiling, with a cheap-model pre-filter so the full debate only runs on high-conflict candidates.

### P1 — this quarter

4. **Persona agents as pluggable alpha models** *(source: ai-hedge-fund)*. Our bull/bear/risk/PM are fixed roles. Add named investor personas (value / quality / momentum / contrarian) as `sys_common_config` rows — consistent with the DB-driven-defaults principle, and it buys the marketing line "14 analysts debated your stock".
5. **Portfolio construction + tearsheets** *(source: cvxpy, quantstats — both Apache-2.0)*. A risk-parity or vol-target overlay on `multi_factor_signals`, plus quantstats tearsheets. Cheapest credibility upgrade available.
6. **Walk-forward harness** *(source: Qlib)*. One runner that re-fits on rolling windows, so `optimize_signals.py` stops overfitting the full history.
7. **Deterministic replay** *(source: nobody — this is ours to invent)*. Pin seed, temperature, model version and prompt hash on every `stock_synthesis` row so any decision replays byte-identically. This is a *governance* feature that happens to also fix reproducibility, and it is the strongest single thing we can build for the BMC/SAP story.

### P2 — opportunistic

8. **OpenBB as an optional provider adapter.** Add `agents/data_providers/openbb.py` behind an env flag. **Do not put it in `requirements.txt`** — AGPL-family licensing.
9. **RD-Agent-style automated factor search.** Only after walk-forward exists; before that it is an overfitting machine.

### Strategy reality check

None of the above makes the signals profitable on its own. The honest read of the field is that public alpha does not exist. Our edge is not "better picks" — it is **auditable picks across 17 markets with a scored, replayable track record**. Point the roadmap there rather than at signal quality alone.

---

## 4. Open source — the decision (revised after founder review, 2026-09-06)

> **Revision note.** The first draft recommended open-sourcing the governance guardrail. Rejected: guardrail is a B2B feature. Its audience is compliance and risk teams, who do not star repositories. Realistic ceiling ~500 stars, and stars are one of the stated goals. The star play has to be 2C. Guardrail is demoted to a quiet enterprise-credibility release with zero star expectation (§4.7).

### Verdict: build a 2C, fork-to-run, self-scoring, APAC-first stock agent. Do not open-source `datapai-stock-be` itself.

### 4.1 What the star data actually rewards

From the two runaway winners, the formula is unambiguous:

- **Forking IS the install.** daily_stock_analysis has a 84% fork-to-star ratio (54.2k / 64.7k) because you fork it to get your own Actions cron and your own secrets. Fork count tracks star count when the install is a fork.
- **Zero infra cost.** GitHub Actions cron, free data sources, free or local LLM tier. No server, no card.
- **Results land in a chat app people already use.** Telegram / Discord / Slack / WeCom.
- **Multi-market.**
- **Five minutes to first result.**

Nothing on that list is about code quality. Our engine is already deeper than daily_stock_analysis's single-pass summariser; depth is not the constraint, packaging is.

### 4.2 The unserved 2C wedge we already own

Two gaps, and both are ours:

**1. Geography.** daily_stock_analysis covers CN / HK / US / JP / KR / TW. TradingAgents and ai-hedge-fund are US-first. **Nobody covers ASX or Southeast Asia.** We already run ASX, SGX, SET, KLSE, IDX, HOSE, HNX, TWSE, HKEX and LSE in production, with per-exchange close times and calendars. Australian and SEA retail investors are a large, underserved, and notably cynical audience with zero open-source option today.

**2. Accountability.** Every AI stock repo in the top 20 makes predictions and never grades itself. We already compute 7/30/90-day forward returns against a benchmark. *"The AI stock agent that publishes its own track record"* is a position no competitor can copy quickly — copying it requires having been publicly wrong for ninety days first.

### 4.3 The product

Working names: **`receipts`** (recommended — "show your receipts" carries the whole positioning), `scorecard`, `hindsight`.

The mechanic, and this is the genuinely novel part:

1. Fork the repo.
2. Set two secrets (an LLM key — free Gemini/DeepSeek tier is fine — and a Telegram bot token).
3. Edit `watchlist.yml`.
4. GitHub Actions runs on a cron per exchange close. We already have those close times in `exchange_registry.py`.
5. **Every call is committed back into your own fork** as a dated JSON + markdown file. Git-timestamped and tamper-evident: you cannot quietly delete a bad prediction.
6. A scoring job re-opens each past call at 7 / 30 / 90 days, computes forward return versus the local index, and regenerates a **GitHub Pages scorecard** in your fork.
7. Results push to Telegram / Discord.

Why this wins on the exact axes that produce stars: forking is mandatory, so forks track stars; the scorecard page is shareable, so distribution is organic; and a git-committed, timestamped track record is a credibility mechanic that no closed-source tool can match — SaaS competitors literally cannot offer it.

### 4.4 The second hook: moomoo trade review

`agents/trade_review/timing_analyzer.py` already produces the emotionally resonant output — *"you bought three days late; it cost you 4.1%."* moomoo/Futu is the dominant retail broker across AU, SG, HK and MY, which is exactly the wedge audience. It runs against a local OpenD gateway, so **no credential ever leaves the user's machine** — a privacy story that plays well with this crowd. Nothing in open source does this. Ship it as an optional module in the same repo.

### 4.5 The open-core line

| Open | Commercial |
|---|---|
| Indicator library (`compute_ta_*`) | Multi-tenant hosted service |
| Exchange registry + calendars | Alerting infrastructure at scale |
| Single-user daily pipeline | TinyFish alt-data agents |
| Scoring + scorecard generator | Governance / audit trail |
| moomoo trade review | CRM + product surface |
| The debate *mechanism* | **The accumulated agent memory** |

The clean line: **open the engine, keep the learned corpus.** Same shape as publishing a model architecture without the checkpoint. `sys_agent_memory` and `sys_agent_results` compound across every ticker we run for every user; a forker starts from zero and gets measurably better results by subscribing. That is the upgrade path, and it is defensible without crippling the free version.

### 4.6 Honest costs and risks

1. **This is a rewrite, not a carve-out.** Five-minute fork-to-run means no Postgres and no FDW. The runtime has to be re-plumbed onto SQLite/DuckDB + parquet with the logic copied across. Budget **3–6 weeks**, not a weekend.
2. **The P0 lookahead fixes become hard prerequisites.** A public scorecard invites scrutiny. If the point-in-time join is wrong, someone will find it, and *that* becomes the story instead of the product.
3. **Dry-run privately for 60–90 days before launch.** If the win rate is a coin flip, publishing it damages the commercial pitch too. Find out before committing to the positioning — and note that the launch asset *is* the accumulated scorecard, so the dry-run period is not a delay, it's the build.
4. **You give away the APAC data plane.** That is the price of the wedge. It is not what we monetise, and holding it back forfeits the only geographic gap in the market.
5. **Actions minutes and repo churn at fork scale.** Proven viable by daily_stock_analysis, but the cron cadence and commit batching need a deliberate rate-limit design.

### 4.7 Revised sequencing

1. **Now** — P0 lookahead + synthetic-data fixes (§3). Prerequisite, not optional.
2. **Weeks 1–6** — build the fork-to-run repo privately; start the scorecard dry-run on day one.
3. **Launch** — when 60–90 days of clean, real scorecard data exist. That data is the launch post.
4. **Quarter 2** — moomoo review module, plus a `tradingagents-datapai` plugin to borrow the 102k-star audience.
5. **Separately and quietly** — Apache-2.0 guardrail release for enterprise credibility. Zero star expectation; it exists to be cited in BMC/SAP conversations, not to trend.

### 4.8 Realistic outcome

With a genuine geographic gap, a novel accountability mechanic, and a working five-minute quickstart: **2,000–10,000 stars in year one** is achievable. Not 64k — daily_stock_analysis had first-mover advantage with a CN audience and WeChat-native distribution we cannot replicate. But the ASX/SEA audience is real, large, and has nothing today.

### 4.9 Pre-release checklist

- [ ] `LICENSE` (MIT — matches 2C peer expectation and maximises fork willingness; Apache-2.0 is for the separate guardrail release)
- [ ] `NOTICE` crediting TauricResearch/TradingAgents for the reflection/memory port in `reflector.py` and `memory.py`
- [ ] `README.md` with a GIF of a Telegram alert and a scorecard page, plus a genuine five-minute quickstart
- [ ] One-click fork template: `watchlist.yml`, `.github/workflows/daily.yml`, two documented secrets
- [ ] GitHub Pages scorecard template that renders from committed JSON
- [ ] Full-history secret scan (`gitleaks detect --log-opts="--all"`)
- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates
- [ ] CI (lint + tests) — a red badge kills adoption
- [ ] `DISCLAIMER.md` — stronger than peers', because we are an AFSL-adjacent brand operating in Australia

---

## 5. Sources

- GitHub REST API, star/fork/license/push data pulled 2026-09-06
- TradingAgents — https://github.com/TauricResearch/TradingAgents
- ai-hedge-fund — https://github.com/virattt/ai-hedge-fund
- daily_stock_analysis — https://github.com/ZhuLinsen/daily_stock_analysis
- Qlib — https://github.com/microsoft/qlib
- OpenBB — https://github.com/OpenBB-finance/OpenBB
- AI agent token-cost economics — https://spendark.com/blog/ai-agent-token-costs/
