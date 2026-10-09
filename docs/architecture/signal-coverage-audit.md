# Signal Coverage Audit — Top Factors That Drive Stock Returns

> **Stance:** Don't tune the engine on a user's hot week. Don't build all 30 factors the literature names.
> **Build the 5–7 factors with the strongest research consensus that we can get cheaply, and have AI distil each one into a single sentence.**

Wide on input — many free public sources. Narrow on output — one line per factor that any reader can follow. That's the synthesis layer that lets the engine actually beat a single-LLM stock-pickern.

---

## Methodology — how factors were chosen

For each candidate signal, I asked:

1. **Academic consensus** — is the factor robust across 30+ years of research, multiple markets?
2. **Practitioner validation** — do real institutional managers use it (IBD, Goldman, Renaissance, AQR)?
3. **Data availability + cost** — free public source preferred; paid data only when irreplaceable.
4. **AI synthesis advantage** — can AI produce a 1-line insight from the raw numbers? If raw value is interpretable on its own (PE = 15), AI doesn't add much. If it requires context (PE 15 vs sector 22 vs 5y history of 18), AI's distillation matters.
5. **What we have already** — don't duplicate.

Anything failing 2 or more of these gets cut. The literature has 100+ "factors" with academic papers; most don't survive practitioner use.

---

## The Top 7 (build in this order)

### 1. Cross-Sectional Momentum (Carhart 12-1)

| | |
|---|---|
| **What** | 12-month return minus most-recent month. *The* canonical momentum factor. |
| **Research** | Jegadeesh-Titman 1993, Carhart 1997, replicated across 200+ years (Geczy-Samonov), 40 markets (Asness-Moskowitz-Pedersen 2013). One of the most robust anomalies known. |
| **Why our RSI/MACD doesn't replace it** | RSI is overbought/oversold over 14 days; MACD is short-term crossover. Neither captures the 12-month relative-strength effect that drives ~3–5% annual alpha. |
| **Data** | Free — already in `datapai.prices`. Just compute. |
| **AI insight (1-line)** | `"Momentum: +34% over 12 months ex last month → top decile; momentum stocks in this percentile delivered avg +18% next 6 months historically"` |

### 2. Relative Strength vs Sector + Market

| | |
|---|---|
| **What** | Stock's return vs its sector ETF + vs S&P 500 over 1/3/6m. Captures "leaders vs laggards." |
| **Research** | IBD's empirical rule that 80% of big winners had RS > 80 at breakout (O'Neil's *How to Make Money in Stocks*). Used systematically by Marketsmith, IBD, William O'Neil + Co. |
| **Why it matters now** | This is what carried SNOW/TEAM/GTLB — they were rallying *with* a leading sector. We can't see that today. |
| **Data** | Free — sector ETFs (XLK, XLF, etc.) + S&P all in price tables. |
| **AI insight (1-line)** | `"Relative strength: +12% above sector (XLK) over 90d; sector itself +8% vs S&P → leading the leader"` |

### 3. Earnings Estimate Revisions Trend

| | |
|---|---|
| **What** | Direction + magnitude of analyst EPS estimate changes over 30/90 days. Are analysts revising up or down? |
| **Research** | One of the most predictive cross-sectional signals known. Cohen-Polk-Vuolteenaho 2003; widely used in factor models (AQR, RBI, Citadel). Drives ~4-6% annual alpha. |
| **Why distinct from analyst consensus** | We capture *current* consensus (BUY/HOLD/SELL). Revisions trend captures the *change* — analysts updating their views = forward-looking. |
| **Data** | Finnhub (already integrated, paid tier covers it) or Yahoo Finance scraping. ~$0.05/call. |
| **AI insight (1-line)** | `"Estimate revisions: 4 of 12 analysts raised FY26 EPS in past 30d, none cut; consensus drifting up — typically precedes positive earnings surprise"` |

### 4. Institutional Sponsorship (13F flow)

| | |
|---|---|
| **What** | Are large funds adding or trimming? SEC 13F filings every quarter; aggregate ownership delta. |
| **Research** | Sias 2004, Daniel-Wermers 2000. Top-of-decile institutional accumulation predicts 6-month outperformance. |
| **The TEAM/SNOW/GTLB pattern** | What you called "money flow" — institutions piled in to SaaS stocks before retail noticed. 13F shows it. |
| **Data** | Free from SEC EDGAR (13F-HR filings). Quarterly lag but informative. Finnhub also exposes aggregated for $. |
| **AI insight (1-line)** | `"Institutional flow: 8 of top-20 holders added in Q1 (vs 2 trimming); concentration up from 62% → 67% of float — accumulation phase"` |

### 5. Quality — Profitability Per Asset (Novy-Marx)

| | |
|---|---|
| **What** | Gross profit / total assets. The *single* most predictive quality metric per Novy-Marx 2013. |
| **Why distinct from ROE** | ROE rewards leverage. Gross profit / assets is cleaner — captures economic efficiency without balance-sheet trickery. |
| **Coverage today** | ⚠️ Partial — our Quality sub-agent uses ROE + margins. Should add GP/Assets as the canonical metric. |
| **Data** | Free — compustat / financial reports we already pull. |
| **AI insight (1-line)** | `"Quality (GP/Assets): 0.42 → top quintile of US large caps; companies in this band returned +4.2% annual excess return 1963-2012"` |

### 6. Short Interest + Days-to-Cover

| | |
|---|---|
| **What** | % of float sold short + how many days of average volume that represents. |
| **Research** | Asquith-Pathak-Ritter 2005; Hanson-Sunderam 2014. High short interest with improving fundamentals → squeeze setup. Persistent high short interest with deteriorating fundamentals → predicts underperformance. |
| **Why it's powerful** | The market's most explicit bearish-positioning indicator. Free, biweekly. |
| **Data** | FINRA biweekly publication — free download. |
| **AI insight (1-line)** | `"Short interest: 18% of float (vs sector median 4%); days-to-cover 5.2 → crowded short; if fundamentals improve, squeeze risk"` |

### 7. Sentiment / Crowd Positioning Composite

| | |
|---|---|
| **What** | Composite of: put/call ratio, Google Trends interest, social-media volume, AAII bull/bear survey. *Contrarian* indicator at extremes. |
| **Research** | Baker-Wurgler 2006 (sentiment index); Da-Engelberg-Gao 2011 ("In Search of Attention" — Google Trends). |
| **Use** | Extremes flag turning points. Generally contrarian — extreme bullish sentiment is a *sell* signal; extreme bearish is a *buy*. |
| **Data** | CBOE put/call (free), Google Trends API (free), AAII (free weekly), Reddit/StockTwits scraping (free). |
| **AI insight (1-line)** | `"Sentiment: Google Trends interest +180% in past 14 days; put/call ratio 0.34 (90th percentile bullish); approaching extreme — contrarian caution warranted"` |

---

## What we already have vs what's missing

| Factor | Status | Effort to add |
|---|---|---|
| Value (PE, PB, EV/EBITDA) | ✅ | n/a |
| Quality — ROE/margins | ✅ | n/a |
| Quality — GP/Assets (Novy-Marx) | ⚠️ | 0.5d — add 1 calc to existing pipeline |
| Momentum (Carhart 12-1) | ❌ | 0.5d — compute from `prices` table |
| Relative Strength (sector + market) | ❌ | 1d — sector ETF lookups + ranking |
| Earnings Revisions Trend | ❌ | 1d — Finnhub API call + delta logic |
| Institutional Sponsorship (13F) | ❌ | 1-2d — SEC EDGAR parse + aggregation |
| Short Interest | ❌ | 0.5d — FINRA file ingest |
| Sentiment Composite | ❌ | 2-3d — multi-source aggregation, hardest to validate |

**Total: ~7-9 days of focused work to close the major gaps.** Not "build everything we hear about."

---

## Build order I'd recommend

Driven purely by research-strength × effort × the gap-it-fills:

1. **Momentum (Carhart 12-1)** — half day, big literature, fills our biggest gap, free data
2. **Relative Strength vs sector + market** — 1 day, exactly the signal that carried SNOW/TEAM/GTLB, free data
3. **Earnings Revisions Trend** — 1 day, very high signal-to-noise, Finnhub integration
4. **Quality: add GP/Assets** — half day, improves existing Quality agent, free
5. **Institutional Sponsorship (13F)** — 1-2 days, lagging but powerful, free
6. **Short Interest** — half day, free, used by every credible quant desk
7. **Sentiment composite** — defer; multi-source aggregation, hardest to validate, returns less stable

After items 1–4 the engine has the canonical academic factor set plus the sector-rotation tailwind that's been killing us. Items 5–7 are nice-to-have.

---

## How AI synthesises wide → narrow

Each new signal produces a raw value. AI's job in the debate is to:

1. **Compare to baselines** — top quintile? sector median? 5y range?
2. **Combine with other signals** — momentum + earnings revisions UP + institutional accumulation = high conviction. Each alone is medium.
3. **Output one sentence per signal** — what any non-quant reader can absorb in 5 seconds.

Today our debate transcripts already do this for the 4 signals we have. Adding the 7 above doesn't make output more complex — Bull/Bear/Risk/PM still produce the same 4 short paragraphs. They just have richer inputs to reason over.

That's the point — **users see the same 4-paragraph debate. The AI's edge grows because it's reasoning over 11 signals instead of 4.**

---

## What this audit deliberately *doesn't* recommend

- ❌ Don't build a "narrative / theme detection agent" — too subjective, hard to validate, regime-dependent. Sector RS captures most of what people mean by "theme rotation."
- ❌ Don't build options-positioning beyond put/call ratio — paid data, marginal alpha vs effort.
- ❌ Don't add macro indicators beyond what `macro_agent` already pulls — they're context, not stock-picking edge.
- ❌ Don't tune existing thresholds in WATCH/AVOID logic until the new signals are landed and Reflector has graded them. Tuning before adding signals = compensating for blindness with calibration.

---

## Open questions for review

1. Are there factors from the AU/HKEX/HOSE practitioner experience you'd add or rank differently?
2. Finnhub paid tier costs ~$50/month — willing to commit for earnings revisions + 13F aggregation?
3. Should Reflector explicitly track per-factor contribution (X% of correct calls had positive momentum signal active) so we can prune factors that don't pay their way in our specific universe?

— Audit drafted 2026-06-01. Treat as a *spec to review*, not a build plan. Code follows after the review pass.
