"""
agents/trade_review/demo_timing.py — run the timing engine on sample trades
against REAL price history. Validates the engine mechanics before the live
moomoo ingest is wired (swap SAMPLE_TRADES for real fills via moomoo_client).

Usage (on EC2, where data providers + deps live):
    python -m agents.trade_review.demo_timing
"""
from __future__ import annotations

from datetime import datetime

from agents.trade_review.timing_analyzer import analyze_trade

# A few illustrative US-equity trades. Replace with real moomoo fills once OpenD
# is up: agents/trade_review/moomoo_client.py -> history_fills().
SAMPLE_TRADES = [
    dict(instrument="NVDA", direction="LONG",
         entry_time=datetime(2025, 4, 9), entry_price=98.0,
         exit_time=datetime(2025, 5, 12),  exit_price=120.0),  # sold a winner early?
    dict(instrument="AAPL", direction="LONG",
         entry_time=datetime(2025, 5, 13), entry_price=212.0,
         exit_time=datetime(2025, 6, 9),  exit_price=201.0),   # bought a local top?
    dict(instrument="TSLA", direction="LONG",
         entry_time=datetime(2025, 3, 25), entry_price=288.0,
         exit_time=None, exit_price=None),                     # still open
]


def main():
    for t in SAMPLE_TRADES:
        v = analyze_trade(suffix="", exchange="US", **t)
        print("=" * 72)
        print(f"{v.instrument} {v.direction}  "
              f"entry {t['entry_price']} -> exit {t.get('exit_price')}")
        es = v.entry_snapshot or {}
        print(f"  entry snapshot: RSI={es.get('d_rsi')} "
              f"ext={es.get('d_ext_atr')}xATR  wRSI={es.get('w_rsi')}")
        print(f"  MAE={v.mae_pct}%  MFE={v.mfe_pct}%  exit_eff={v.exit_efficiency}")
        print(f"  ENTRY: {v.entry_timing} ({v.entry_timing_score})")
        print(f"  EXIT : {v.exit_timing} ({v.exit_timing_score})")
        for r in v.reasons:
            print(f"     - {r}")


if __name__ == "__main__":
    main()
