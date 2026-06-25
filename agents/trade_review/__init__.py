"""
agents/trade_review — Feature A: per-trade analysis (AI Trade Council variant).

Reuses the AG2 GroupChat orchestration from `agents.stock_synthesis`, swapping
the Bull/Bear/Risk/PM personas for Performance / Risk / Rotation Reviewer +
Trade Manager. Reviews a single open or closed client trade against the signal
state at entry and now, plus the live AI Trade Council verdict on the instrument.

See docs (datapai-cfd-be):
  docs/architecture/2026-06-25-ai-trade-portfolio-analysis-design.md  (§3)
"""
