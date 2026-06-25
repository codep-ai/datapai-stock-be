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
    dict(instrument="AAPL", direction="LONG",
         entry_time=datetime(2024, 7, 15), entry_price=234.0,
         exit_time=datetime(2024, 8, 5),  exit_price=209.0),   # bought near a local top
    dict(instrument="NVDA", direction="LONG",
         entry_time=datetime(2024, 8, 7), entry_price=98.0,
         exit_time=datetime(2024, 9, 6),  exit_price=102.0),   # sold a winner early?
    dict(instrument="MSFT", direction="LONG",
         entry_time=datetime(2024, 1, 8), entry_price=375.0,
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
