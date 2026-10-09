-- migrations/052_user_trades.sql
-- 2026-06-25 — Per-user trade ingest tables for the trade-intelligence feature.
--
-- WHY
--   Feature A (per-trade analysis) + the per-user behavioural / lessons layer
--   (design §9) need each end user's real fills and round-trip trades. The
--   bootstrap source is moomoo OpenAPI (Donny's own account); the schema is
--   broker-agnostic so a brokerage trade feed can land here too.
--
--   Two grains:
--     user_fills   — one row per execution (raw, from moomoo history_deal_list)
--     fct_user_trades — one row per round-trip trade (entry+exit paired), the
--                       grain the trade_review personas + stats run over.
--
-- WHERE
--   stock-db (datapai_stock). source_account lets one user hold multiple
--   broker accounts. user_id is the platform auth user.
--
-- ROLLBACK (manual):
--   DROP TABLE IF EXISTS datapai.fct_user_trades;
--   DROP TABLE IF EXISTS datapai.user_fills;

BEGIN;

-- ╭───────────────────────────────────────────────────────────────────────╮
-- │ user_fills — one row per execution (raw)                              │
-- ╰───────────────────────────────────────────────────────────────────────╯
CREATE TABLE IF NOT EXISTS datapai.user_fills (
    fill_pk         BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    source          VARCHAR(20) NOT NULL DEFAULT 'moomoo',   -- moomoo / broker_feed / ...
    source_account  TEXT,                                    -- moomoo acc_id / broker acct
    deal_id         TEXT NOT NULL,                           -- broker's unique fill id
    order_id        TEXT,
    instrument      TEXT NOT NULL,                           -- e.g. US.AAPL
    name            TEXT,
    side            VARCHAR(8) NOT NULL,                     -- BUY / SELL
    qty             NUMERIC(20, 4) NOT NULL,
    price           NUMERIC(20, 6) NOT NULL,
    currency        VARCHAR(8),
    fill_time       TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- idempotent re-ingest: a fill is unique per (source, account, deal_id)
    CONSTRAINT uq_user_fills_dedup UNIQUE (source, source_account, deal_id)
);

CREATE INDEX IF NOT EXISTS idx_user_fills_user_time
    ON datapai.user_fills (user_id, fill_time DESC);
CREATE INDEX IF NOT EXISTS idx_user_fills_instrument
    ON datapai.user_fills (user_id, instrument, fill_time);

-- ╭───────────────────────────────────────────────────────────────────────╮
-- │ fct_user_trades — one row per round-trip trade (paired entry+exit)     │
-- ╰───────────────────────────────────────────────────────────────────────╯
CREATE TABLE IF NOT EXISTS datapai.fct_user_trades (
    trade_pk        BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    source          VARCHAR(20) NOT NULL DEFAULT 'moomoo',
    source_account  TEXT,
    instrument      TEXT NOT NULL,
    name            TEXT,
    direction       VARCHAR(8) NOT NULL,                     -- LONG / SHORT
    qty             NUMERIC(20, 4) NOT NULL,
    leverage        NUMERIC(8, 2),                           -- NULL for cash equity

    entry_price     NUMERIC(20, 6) NOT NULL,
    entry_time      TIMESTAMPTZ NOT NULL,
    exit_price      NUMERIC(20, 6),                          -- NULL = still open
    exit_time       TIMESTAMPTZ,

    realised_pnl    NUMERIC(20, 4) NOT NULL DEFAULT 0,
    unrealised_pnl  NUMERIC(20, 4) NOT NULL DEFAULT 0,
    currency        VARCHAR(8),
    holding_secs    BIGINT,                                  -- exit_time - entry_time

    -- Filled in by the analysis layer (trade_review verdict + §9 stats)
    r_multiple      NUMERIC(10, 4),
    process_grade   VARCHAR(2),                              -- A..F
    review_verdict  JSONB,                                   -- TradeReviewVerdict
    detected_mistakes TEXT[],

    -- Provenance: which fills compose this round-trip
    entry_fill_ids  BIGINT[],
    exit_fill_ids   BIGINT[],

    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fct_user_trades_user_time
    ON datapai.fct_user_trades (user_id, entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_fct_user_trades_open
    ON datapai.fct_user_trades (user_id) WHERE exit_time IS NULL;
CREATE INDEX IF NOT EXISTS idx_fct_user_trades_instrument
    ON datapai.fct_user_trades (user_id, instrument);

COMMENT ON TABLE datapai.user_fills IS
'Raw per-execution fills per end user (bootstrap source: moomoo OpenAPI). '
'Idempotent on (source, source_account, deal_id).';
COMMENT ON TABLE datapai.fct_user_trades IS
'Round-trip trades (paired entry+exit) per end user — grain for trade_review '
'personas and the per-user behavioural / lessons / stats layer (design §9).';

-- Verification:
--   SELECT count(*) FROM datapai.user_fills;
--   SELECT user_id, count(*), sum(realised_pnl) FROM datapai.fct_user_trades GROUP BY 1;

COMMIT;
