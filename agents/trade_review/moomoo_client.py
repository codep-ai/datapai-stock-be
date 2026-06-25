"""
agents/trade_review/moomoo_client.py — thin wrapper over the moomoo / Futu
OpenAPI SDK to pull a user's real trade history, positions, and account info.

Runs against a local **OpenD** gateway (default 127.0.0.1:11111) that is logged
into the user's moomoo account. We never store the moomoo login here — OpenD
holds the session; this client only knows the OpenD host/port and (for real
trades) the trade-unlock password, supplied via env at runtime.

SDK: the `moomoo` pip package (US/intl) or the near-identical `futu` package.
We import whichever is present.

Docs:
  https://openapi.moomoo.com/moomoo-api-doc/en/trade/overview.html
  https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-history-order-fill-list.html
  https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-position-list.html

Design: datapai-cfd-be docs/architecture/2026-06-25-ai-trade-portfolio-
analysis-design.md (§10).
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional

# The moomoo and futu SDKs expose the same symbols. Prefer `moomoo`.
try:  # pragma: no cover - import resolved on EC2 where the SDK is installed
    import moomoo as ft
except ImportError:  # pragma: no cover
    import futu as ft


# Market → SDK enum. moomoo US accounts use SecurityFirm.FUTUINC.
_TRD_MARKET = {
    "US": ft.TrdMarket.US,
    "HK": ft.TrdMarket.HK,
    "CN": ft.TrdMarket.CN,
    "AU": getattr(ft.TrdMarket, "AU", ft.TrdMarket.US),
}


class MoomooClient:
    """
    Connect to OpenD and pull trade history / positions / account info.

    Usage (on EC2, with OpenD running and logged in):
        client = MoomooClient(market="US", trd_env="REAL")
        client.connect()
        fills = client.history_fills(days=365)
        positions = client.positions()
        client.close()

    Env vars:
        MOOMOO_OPEND_HOST   (default 127.0.0.1)
        MOOMOO_OPEND_PORT   (default 11111)
        MOOMOO_TRADE_PWD    plaintext trade-unlock password (REAL env only).
                            Hashed to MD5 before it leaves this process.
    """

    def __init__(
        self,
        market: str = "US",
        trd_env: str = "REAL",
        host: Optional[str] = None,
        port: Optional[int] = None,
        acc_id: int = 0,
    ):
        self.market = market.upper()
        self.trd_env = ft.TrdEnv.REAL if trd_env.upper() == "REAL" else ft.TrdEnv.SIMULATE
        self.host = host or os.getenv("MOOMOO_OPEND_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("MOOMOO_OPEND_PORT", "11111"))
        self.acc_id = acc_id  # 0 = first account on the connection
        self._trd_ctx = None

    # ── connection ──────────────────────────────────────────────────────
    def connect(self) -> "MoomooClient":
        kwargs = dict(
            filter_trdmarket=_TRD_MARKET.get(self.market, ft.TrdMarket.US),
            host=self.host,
            port=self.port,
        )
        # moomoo US requires the security_firm; default to FUTUINC where present.
        if hasattr(ft, "SecurityFirm"):
            kwargs["security_firm"] = getattr(
                ft.SecurityFirm, "FUTUINC", ft.SecurityFirm.FUTUSECURITIES
            )
        self._trd_ctx = ft.OpenSecTradeContext(**kwargs)

        if self.trd_env == ft.TrdEnv.REAL:
            self._unlock()
        return self

    def _unlock(self) -> None:
        pwd = os.getenv("MOOMOO_TRADE_PWD")
        if not pwd:
            raise RuntimeError(
                "REAL trade env needs MOOMOO_TRADE_PWD (the moomoo trade-unlock "
                "password) to unlock_trade(). Set it in the EC2 env, not in code."
            )
        pwd_md5 = hashlib.md5(pwd.encode()).hexdigest()
        ret, data = self._trd_ctx.unlock_trade(password_md5=pwd_md5)
        if ret != ft.RET_OK:
            raise RuntimeError(f"unlock_trade failed: {data}")

    def close(self) -> None:
        if self._trd_ctx is not None:
            self._trd_ctx.close()
            self._trd_ctx = None

    # ── queries ─────────────────────────────────────────────────────────
    def history_fills(self, days: int = 365):
        """
        Historical filled deals — the core dataset for per-trade analysis.
        Returns the SDK DataFrame (code, stock_name, trd_side, qty, price,
        create_time, deal_id, order_id, ...).
        """
        end = datetime.now()
        start = end - timedelta(days=days)
        ret, data = self._trd_ctx.history_deal_list_query(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            trd_env=self.trd_env,
            acc_id=self.acc_id,
        )
        if ret != ft.RET_OK:
            raise RuntimeError(f"history_deal_list_query failed: {data}")
        return data

    def history_orders(self, days: int = 365):
        end = datetime.now()
        start = end - timedelta(days=days)
        ret, data = self._trd_ctx.history_order_list_query(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            trd_env=self.trd_env,
            acc_id=self.acc_id,
        )
        if ret != ft.RET_OK:
            raise RuntimeError(f"history_order_list_query failed: {data}")
        return data

    def positions(self):
        ret, data = self._trd_ctx.position_list_query(
            trd_env=self.trd_env, acc_id=self.acc_id
        )
        if ret != ft.RET_OK:
            raise RuntimeError(f"position_list_query failed: {data}")
        return data

    def account(self):
        ret, data = self._trd_ctx.accinfo_query(
            trd_env=self.trd_env, acc_id=self.acc_id
        )
        if ret != ft.RET_OK:
            raise RuntimeError(f"accinfo_query failed: {data}")
        return data

    # ── normalisation ───────────────────────────────────────────────────
    @staticmethod
    def fills_to_records(df) -> list[dict]:
        """
        Normalise the SDK fills DataFrame into plain dicts keyed for the
        ingest layer / TradeInput. One record per fill; pairing fills into
        round-trip trades (entry+exit) happens downstream in ingest_moomoo.
        """
        cols = {
            "deal_id": "deal_id",
            "order_id": "order_id",
            "code": "instrument",
            "stock_name": "name",
            "trd_side": "side",        # BUY / SELL
            "qty": "qty",
            "price": "price",
            "create_time": "fill_time",
        }
        records = []
        for _, row in df.iterrows():
            rec = {dst: row.get(src) for src, dst in cols.items() if src in df.columns}
            records.append(rec)
        return records
