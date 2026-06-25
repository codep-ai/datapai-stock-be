"""
agents/trade_review/timing_analyzer.py — deterministic per-trade timing engine.

The core of the validation spike. For one trade it:
  1. binds the POINT-IN-TIME daily + weekly TA snapshot at entry and exit
     (no lookahead — indicators computed on OHLCV truncated at the fill date),
  2. computes MAE/MFE from the realised price path,
  3. judges whether the entry/exit was too early / too late with transparent
     deterministic rules → scores (the warehouse computes; the LLM only explains).

Design: datapai-cfd-be docs/architecture/
  2026-06-25-trade-intelligence-signal-binding-and-learning.md (§2, §3).

Deliberately NO LLM call and NO debate here — bulk history must be cheap and
deterministic (see the design-critique doc, correction #2). The AG2 debate is
reserved for the live open-position "second opinion".
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from agents.technical_analysis import fetch_ohlcv, calc_indicators


# ── point-in-time snapshot ──────────────────────────────────────────────────
def _to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample a daily OHLCV frame to weekly bars (W-FRI)."""
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    cols = {k: v for k, v in agg.items() if k in df.columns}
    return df.resample("W-FRI").agg(cols).dropna(how="any")


def _truncate(df: pd.DataFrame, as_of: datetime) -> pd.DataFrame:
    """Bars up to AND INCLUDING as_of — the no-lookahead guarantee."""
    ts = pd.Timestamp(as_of)
    return df.loc[df.index <= ts]


def point_in_time_snapshot(daily: pd.DataFrame, as_of: datetime) -> dict:
    """
    Daily + weekly indicator state as known at `as_of`. Returns a flat dict of
    the fields the timing rules use; values are None when there's too little
    history (callers must null-check).
    """
    d = _truncate(daily, as_of)
    if len(d) < 26:  # need enough bars for MACD
        return {"insufficient_history": True}

    di = calc_indicators(d)
    wk = _truncate(_to_weekly(daily), as_of)
    wi = calc_indicators(wk) if len(wk) >= 26 else {}

    def g(src: dict, *keys):
        for k in keys:
            if src.get(k) is not None:
                return src[k]
        return None

    price = g(di, "current_price")
    ema20, ema50, ema200 = g(di, "ema_20"), g(di, "ema_50"), g(di, "ema_200")
    atr = g(di, "atr", "atr_14")
    return {
        "as_of": pd.Timestamp(as_of).date().isoformat(),
        "price": price,
        # daily
        "d_rsi": g(di, "rsi", "rsi_14"),
        "d_macd_line": g(di, "macd_line"),
        "d_macd_sig": g(di, "macd_sig", "macd_signal"),
        "d_macd_hist": g(di, "macd_hist"),
        "d_ema20": ema20, "d_ema50": ema50, "d_ema200": ema200,
        "d_atr": atr,
        # extension above/below the 20-EMA, in ATR units (how "far" is far)
        "d_ext_atr": (round((price - ema20) / atr, 2) if price and ema20 and atr else None),
        # weekly
        "w_rsi": g(wi, "rsi", "rsi_14"),
        "w_macd_line": g(wi, "macd_line"),
        "w_macd_hist": g(wi, "macd_hist"),
    }


# ── MAE / MFE from the realised path ────────────────────────────────────────
def _mae_mfe(daily: pd.DataFrame, entry_time, exit_time, direction: str, entry_price: float):
    """Max adverse / favourable excursion (as % of entry) over the holding window."""
    seg = daily.loc[(daily.index >= pd.Timestamp(entry_time)) &
                    (daily.index <= pd.Timestamp(exit_time or daily.index[-1]))]
    if seg.empty or not entry_price:
        return None, None
    long = direction.upper() == "LONG"
    fav = (seg["High"].max() - entry_price) if long else (entry_price - seg["Low"].min())
    adv = (entry_price - seg["Low"].min()) if long else (seg["High"].max() - entry_price)
    return round(adv / entry_price * 100, 2), round(fav / entry_price * 100, 2)


# ── verdict ─────────────────────────────────────────────────────────────────
@dataclass
class TimingVerdict:
    instrument: str
    direction: str
    entry_snapshot: dict = field(default_factory=dict)
    exit_snapshot: Optional[dict] = None
    mae_pct: Optional[float] = None
    mfe_pct: Optional[float] = None
    entry_timing: str = "unknown"        # well_timed / chased / early_knife / fine
    entry_timing_score: Optional[float] = None
    exit_timing: str = "unknown"         # well_timed / sold_early / held_late / open / fine
    exit_timing_score: Optional[float] = None
    exit_efficiency: Optional[float] = None
    reasons: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _judge_entry(s: dict, direction: str) -> tuple[str, float, list]:
    """Transparent entry-timing rules over the point-in-time snapshot."""
    if s.get("insufficient_history"):
        return "unknown", None, ["insufficient price history at entry"]
    long = direction.upper() == "LONG"
    rsi, ext, macd_hist = s.get("d_rsi"), s.get("d_ext_atr"), s.get("d_macd_hist")
    reasons = []
    # CHASED: overbought + extended far above the mean, with-trend
    if long and rsi is not None and ext is not None and rsi > 70 and ext > 2.5:
        reasons.append(f"entered at RSI {rsi:.0f}, {ext:.1f}×ATR above EMA20 — extended")
        return "chased", 0.25, reasons
    if not long and rsi is not None and ext is not None and rsi < 30 and ext < -2.5:
        reasons.append(f"shorted at RSI {rsi:.0f}, {abs(ext):.1f}×ATR below EMA20 — extended")
        return "chased", 0.25, reasons
    # FALLING KNIFE: counter-trend into negative momentum
    if long and macd_hist is not None and rsi is not None and macd_hist < 0 and rsi < 40:
        reasons.append(f"bought into weakness — MACD hist {macd_hist:.2f}, RSI {rsi:.0f}")
        return "early_knife", 0.4, reasons
    # WELL-TIMED: momentum turning up near the mean
    if long and macd_hist is not None and macd_hist > 0 and rsi is not None and 45 <= rsi <= 65:
        reasons.append(f"momentum up, RSI {rsi:.0f} — constructive entry")
        return "well_timed", 0.8, reasons
    return "fine", 0.6, reasons or ["no strong timing signal at entry"]


def _judge_exit(s: Optional[dict], direction: str, mfe_pct, captured_pct) -> tuple[str, float, float, list]:
    if s is None:
        return "open", None, None, ["position still open"]
    if s.get("insufficient_history"):
        return "unknown", None, None, ["insufficient price history at exit"]
    reasons = []
    eff = None
    if mfe_pct and mfe_pct > 0 and captured_pct is not None:
        eff = round(max(0.0, min(1.0, captured_pct / mfe_pct)), 2)
    long = direction.upper() == "LONG"
    rsi, macd_hist = s.get("d_rsi"), s.get("d_macd_hist")
    # SOLD EARLY (A): exited a winner while momentum still strong
    if long and macd_hist is not None and macd_hist > 0 and rsi is not None and rsi < 65 \
            and eff is not None and eff < 0.5:
        reasons.append(f"exited at RSI {rsi:.0f} with momentum still positive; "
                       f"captured {eff:.0%} of the favourable move")
        return "sold_early", 0.3, eff, reasons
    # SOLD EARLY (B): left most of a real move on the table, regardless of exit momentum
    if eff is not None and eff < 0.35 and mfe_pct is not None and mfe_pct > 5:
        reasons.append(f"captured only {eff:.0%} of a {mfe_pct:.0f}% favourable move "
                       f"— exited well before the move was done")
        return "sold_early", 0.35, eff, reasons
    # HELD LATE: exited a loser only after momentum broke down hard
    if long and macd_hist is not None and macd_hist < 0 and rsi is not None and rsi < 35:
        reasons.append(f"exited deep into weakness — RSI {rsi:.0f}, MACD hist {macd_hist:.2f}")
        return "held_late", 0.35, eff, reasons
    return "fine", 0.6, eff, reasons or ["no strong timing signal at exit"]


def analyze_trade(
    instrument: str,
    direction: str,
    entry_time: datetime,
    entry_price: float,
    exit_time: Optional[datetime] = None,
    exit_price: Optional[float] = None,
    *,
    suffix: str = "",
    exchange: Optional[str] = None,
    daily: Optional[pd.DataFrame] = None,
) -> TimingVerdict:
    """
    Analyse one trade's timing against point-in-time TA. `daily` can be passed in
    to avoid re-fetching when batching many trades on the same instrument.
    """
    if daily is None:
        daily = fetch_ohlcv(instrument, timeframe="1d", suffix=suffix, exchange=exchange)
    v = TimingVerdict(instrument=instrument, direction=direction)
    if daily is None or daily.empty:
        v.reasons.append("no price history available")
        return v
    daily = daily.sort_index()

    v.entry_snapshot = point_in_time_snapshot(daily, entry_time)
    if exit_time is not None:
        v.exit_snapshot = point_in_time_snapshot(daily, exit_time)

    v.mae_pct, v.mfe_pct = _mae_mfe(daily, entry_time, exit_time, direction, entry_price)

    v.entry_timing, v.entry_timing_score, er = _judge_entry(v.entry_snapshot, direction)
    v.reasons += er

    captured = None
    if exit_price and entry_price:
        captured = round((exit_price - entry_price) / entry_price * 100, 2)
        if direction.upper() == "SHORT":
            captured = -captured
    v.exit_timing, v.exit_timing_score, v.exit_efficiency, xr = _judge_exit(
        v.exit_snapshot, direction, v.mfe_pct, captured
    )
    v.reasons += xr
    return v
