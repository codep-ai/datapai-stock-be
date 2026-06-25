"""
agents/trade_review/contracts.py — Pydantic models for per-trade analysis.

Mirrors agents/stock_synthesis/contracts.py. The verdict schema follows the
Feature A design in datapai-cfd-be docs/architecture/2026-06-25-ai-trade-
portfolio-analysis-design.md (§3).
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TradeAction(str, Enum):
    """What the Trade Manager recommends doing with this specific position."""
    HOLD          = "HOLD"           # keep as-is
    ADD           = "ADD"            # scale in
    PARTIAL_CLOSE = "PARTIAL_CLOSE"  # take some off
    FULL_CLOSE    = "FULL_CLOSE"     # exit entirely
    ROLL          = "ROLL"           # roll to a different expiry / strike / instrument
    HEDGE         = "HEDGE"          # offset with a hedge rather than close


class ProcessGrade(str, Enum):
    """
    Quality of the trade ON PROCESS, independent of outcome. The differentiator
    no retail journal frames as a reasoned verdict — separates luck from skill.
    A profitable trade can still be D/F if it ignored the plan and got bailed
    out by a move; a losing trade can be A if entry/sizing/exit were all correct.
    """
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class ClientTier(str, Enum):
    """AFSL advice-gating tier. Drives the governance pre/post-screen."""
    RETAIL    = "RETAIL"     # general-advice framing + disclaimer; no personal advice
    WHOLESALE = "WHOLESALE"  # fuller framing permitted


class TradeInput(BaseModel):
    """The client trade under review + the signal context the personas read."""
    instrument: str = Field(description="Ticker / FX pair / index / commodity")
    exchange: str = Field(default="", description="Venue or asset class")
    direction: str = Field(description="LONG or SHORT")
    size: float = Field(description="Position size (units / contracts / notional)")
    leverage: Optional[float] = Field(default=None, description="Leverage used (CFD/FX)")
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float] = Field(default=None, description="None if still open")
    exit_time: Optional[datetime] = None
    current_price: Optional[float] = Field(default=None, description="Mark for open trades")
    realised_pnl: float = Field(default=0.0)
    unrealised_pnl: float = Field(default=0.0)
    account_equity: Optional[float] = Field(default=None, description="For sizing/risk %")
    client_tier: ClientTier = ClientTier.RETAIL

    # Signal context (joined upstream from the TA/FA marts)
    signal_at_entry: dict = Field(
        default_factory=dict,
        description="TA/FA snapshot at entry_time: {rsi, macd, trend, support, ...}",
    )
    signal_now: dict = Field(
        default_factory=dict,
        description="TA/FA snapshot at current/exit time",
    )
    council_verdict: dict = Field(
        default_factory=dict,
        description="Current AI Trade Council verdict on this instrument "
                    "{direction, confidence, conviction, invalidation_level}",
    )


class PnlAttribution(BaseModel):
    """Decompose P&L into its drivers. fx is non-zero for CFD/FX trades."""
    direction: float = Field(default=0.0, description="P&L from the price move itself")
    timing: float = Field(default=0.0, description="P&L gained/lost vs ideal entry/exit timing")
    sizing: float = Field(default=0.0, description="P&L impact of the chosen size")
    fx: float = Field(default=0.0, description="P&L from the currency leg (CFD/FX)")


class MaeMfe(BaseModel):
    """Max adverse / favourable excursion, in R units, + exit efficiency."""
    mae_R: float = Field(default=0.0, description="Worst drawdown during the trade, in R")
    mfe_R: float = Field(default=0.0, description="Best unrealised gain during the trade, in R")
    exit_efficiency: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Captured gain / max favourable excursion (1.0 = perfect exit)",
    )


class TradeReviewVerdict(BaseModel):
    """Final synthesised per-trade verdict from the Trade Manager."""
    instrument: str
    exchange: str = ""

    action: TradeAction
    confidence: float = Field(ge=0.0, le=1.0)
    conviction: str = Field(description="HIGH / MEDIUM / LOW")

    # Process quality (luck vs skill)
    process_grade: ProcessGrade
    entry_timing_score: float = Field(ge=0.0, le=1.0, description="Quality of entry timing vs signals")
    exit_timing_score: float = Field(ge=0.0, le=1.0, description="Quality of exit timing (0 if still open)")

    # Attribution + excursion
    pnl_attribution: PnlAttribution = Field(default_factory=PnlAttribution)
    mae_mfe: MaeMfe = Field(default_factory=MaeMfe)
    r_multiple: Optional[float] = Field(default=None, description="Realised P&L in R (risk) units")

    # Coaching
    detected_mistakes: List[str] = Field(
        default_factory=list,
        description="e.g. oversized, cut_winner_early, revenge_trade, chased_entry, no_stop",
    )
    key_risk: str = Field(description="Primary live risk on this position")
    recommended_exit_level: Optional[float] = Field(default=None, description="Suggested stop/exit price")
    council_alignment: str = Field(default="n/a", description="agrees | conflicts | n/a")
    thesis: str = Field(description="2-3 sentence reasoned verdict")

    # Governance + metadata
    client_tier: ClientTier = ClientTier.RETAIL
    advice_framing: str = Field(
        default="general_advice",
        description="general_advice (retail) | wholesale — set by the governance gate",
    )
    governance_disclaimer: Optional[str] = Field(default=None)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(default="gemini-2.5-flash")
    total_tokens: int = Field(default=0)
