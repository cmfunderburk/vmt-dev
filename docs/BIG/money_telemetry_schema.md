### Money Telemetry Database Schema Extensions

Author: VMT Assistant
Date: 2025-10-19

This document specifies all database schema changes required to support money tracking in VMT's telemetry system, aligned with the Money SSOT Implementation Plan.

---

## Overview

The money extension adds three layers of telemetry:
1. **Mode/regime tracking** — tick-level state of active exchange types
2. **Money inventories** — per-agent M holdings
3. **Monetary trades** — trades involving money with λ context

All changes are **backward compatible** — legacy runs without money will have NULL or 0 values in new columns.

---

## Schema Changes

### 1) Extend `simulation_runs` table

Add columns to track money configuration:

```sql
ALTER TABLE simulation_runs ADD COLUMN exchange_regime TEXT DEFAULT 'barter_only';
ALTER TABLE simulation_runs ADD COLUMN money_mode TEXT DEFAULT NULL;
ALTER TABLE simulation_runs ADD COLUMN money_scale INTEGER DEFAULT 1;
```

**Purpose**: Record money configuration for each run in metadata

**Values**:
- `exchange_regime`: "barter_only", "money_only", "mixed", "mixed_liquidity_gated"
- `money_mode`: "quasilinear", "kkt_lambda", or NULL for non-money runs
- `money_scale`: integer ≥ 1 for minor units conversion

---

### 2) Extend `agent_snapshots` table

Add money-related state columns:

```sql
ALTER TABLE agent_snapshots ADD COLUMN inventory_M INTEGER DEFAULT 0;
ALTER TABLE agent_snapshots ADD COLUMN lambda_money REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN ask_A_in_M REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN bid_A_in_M REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN ask_B_in_M REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN bid_B_in_M REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN perceived_price_A REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN perceived_price_B REAL DEFAULT NULL;
ALTER TABLE agent_snapshots ADD COLUMN lambda_changed INTEGER DEFAULT 0;
```

**Purpose**: Track per-agent money holdings, quotes, and λ state

**Column details**:
- `inventory_M`: Money holdings in minor units (always ≥ 0)
- `lambda_money`: Marginal utility of money (NULL for non-money runs)
- `ask_*_in_M`, `bid_*_in_M`: Reservation prices in money terms (NULL if `exchange_regime = "barter_only"`)
- `perceived_price_A/B`: Aggregated neighbor prices (KKT mode only)
- `lambda_changed`: Boolean flag (0/1) indicating if λ was updated this tick

**Indices**:
```sql
CREATE INDEX IF NOT EXISTS idx_agent_snapshots_money 
ON agent_snapshots(run_id, tick, inventory_M, lambda_money);
```

---

### 3) Extend `trades` table

Add money-related trade information:

```sql
ALTER TABLE trades ADD COLUMN dM INTEGER DEFAULT 0;
ALTER TABLE trades ADD COLUMN exchange_pair_type TEXT DEFAULT 'A<->B';
ALTER TABLE trades ADD COLUMN buyer_lambda REAL DEFAULT NULL;
ALTER TABLE trades ADD COLUMN seller_lambda REAL DEFAULT NULL;
ALTER TABLE trades ADD COLUMN buyer_surplus REAL DEFAULT NULL;
ALTER TABLE trades ADD COLUMN seller_surplus REAL DEFAULT NULL;
```

**Purpose**: Record monetary flows and surplus decomposition

**Column details**:
- `dM`: Money transfer amount (positive = buyer paid seller; 0 for barter)
- `exchange_pair_type`: One of "A<->B", "A<->M", "B<->M", "M<->A", "M<->B", "B<->A"
- `buyer_lambda`, `seller_lambda`: λ values at trade time (NULL for barter)
- `buyer_surplus`, `seller_surplus`: ΔU for each party (always positive per SSOT)

**Derived price calculation**:
- For barter (A↔B): `price = dB / dA` (existing behavior)
- For monetary (A↔M): `price = dM / dA` (money per good)
- For monetary (B↔M): `price = dM / dB` (money per good)

**Indices**:
```sql
CREATE INDEX IF NOT EXISTS idx_trades_money 
ON trades(run_id, tick, exchange_pair_type, dM);

CREATE INDEX IF NOT EXISTS idx_trades_surplus 
ON trades(run_id, buyer_surplus, seller_surplus);
```

---

### 4) New `tick_states` table

Track combined mode+regime state per tick:

```sql
CREATE TABLE IF NOT EXISTS tick_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    current_mode TEXT NOT NULL,
    exchange_regime TEXT NOT NULL,
    active_pairs TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id),
    UNIQUE(run_id, tick)
);

CREATE INDEX IF NOT EXISTS idx_tick_states_run_tick 
ON tick_states(run_id, tick);

CREATE INDEX IF NOT EXISTS idx_tick_states_mode 
ON tick_states(run_id, current_mode, exchange_regime);
```

**Purpose**: Log the effective exchange environment per tick (Option A-plus observability)

**Column details**:
- `current_mode`: "forage" | "trade" | "both" (from `mode_schedule`)
- `exchange_regime`: "barter_only" | "money_only" | "mixed" | "mixed_liquidity_gated"
- `active_pairs`: JSON array of active pair types, e.g., `["A<->M", "B<->M"]` or `["A<->B"]`

**Example rows**:
```
tick=5, mode="forage", regime="money_only", active_pairs="[]"
tick=6, mode="trade", regime="money_only", active_pairs='["A<->M","B<->M"]'
tick=20, mode="trade", regime="mixed", active_pairs='["A<->M","B<->M","A<->B"]'
```

---

### 5) New `lambda_updates` table (KKT mode only)

Track λ estimation diagnostics:

```sql
CREATE TABLE IF NOT EXISTS lambda_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    tick INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    lambda_old REAL NOT NULL,
    lambda_new REAL NOT NULL,
    lambda_hat_A REAL NOT NULL,
    lambda_hat_B REAL NOT NULL,
    lambda_hat REAL NOT NULL,
    clamped INTEGER NOT NULL,
    clamp_type TEXT,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_lambda_updates_run_agent 
ON lambda_updates(run_id, agent_id, tick);
```

**Purpose**: Debug and validate KKT λ smoothing behavior

**Column details**:
- `lambda_old`: λ before update
- `lambda_new`: λ after update (post-smoothing and clamping)
- `lambda_hat_A`, `lambda_hat_B`: Intermediate estimates from MU_A/p̂_A and MU_B/p̂_B
- `lambda_hat`: min(λ_hat_A, λ_hat_B) before smoothing
- `clamped`: Boolean (0/1) whether bounds were hit
- `clamp_type`: "lower", "upper", or NULL

**Logging condition**: Only log when `|lambda_new - lambda_old| > epsilon` (avoid spam)

---

### 6) Extend `decisions` table

Add exchange regime context:

```sql
-- This column already exists in current schema (from mode_schedule implementation)
-- Just document its expanded semantics:
-- mode: "forage" | "trade" | "both"  (temporal control)
```

No schema change needed — the existing `mode` column captures temporal state.
For type control (exchange_regime), query `tick_states.exchange_regime` by join on `(run_id, tick)`.

---

### 7) Extend `trade_attempts` table (debug mode)

Add money-specific diagnostics:

```sql
ALTER TABLE trade_attempts ADD COLUMN exchange_pair_type TEXT DEFAULT 'A<->B';
ALTER TABLE trade_attempts ADD COLUMN dM_attempted INTEGER DEFAULT 0;
ALTER TABLE trade_attempts ADD COLUMN buyer_lambda REAL DEFAULT NULL;
ALTER TABLE trade_attempts ADD COLUMN seller_lambda REAL DEFAULT NULL;
ALTER TABLE trade_attempts ADD COLUMN buyer_M_init INTEGER DEFAULT 0;
ALTER TABLE trade_attempts ADD COLUMN seller_M_init INTEGER DEFAULT 0;
ALTER TABLE trade_attempts ADD COLUMN buyer_M_final INTEGER DEFAULT 0;
ALTER TABLE trade_attempts ADD COLUMN seller_M_final INTEGER DEFAULT 0;
```

**Purpose**: Debug money trade failures

**Column details**:
- `exchange_pair_type`: Attempted pair type
- `dM_attempted`: Attempted money transfer
- `buyer/seller_lambda`: λ values at attempt time
- `buyer/seller_M_init/final`: Money inventories before/after

---

## Migration Strategy

### Phase 1a: Add columns with defaults (backward compatible)

All `ALTER TABLE` statements use `DEFAULT` to ensure existing runs are unaffected:
- New integer columns default to 0
- New text columns default to NULL or appropriate legacy value
- Existing queries continue working

### Phase 1b: Create new tables

New tables (`tick_states`, `lambda_updates`) only receive data from money-enabled runs.

### Phase 1c: Update insert statements

Modify telemetry loggers to populate new columns:
- Check if money is enabled (`exchange_regime != "barter_only"`)
- If yes, populate money columns; otherwise leave as defaults

---

## Query Examples

### Q1: Find all monetary trades in a run
```sql
SELECT * FROM trades 
WHERE run_id = ? AND dM > 0 
ORDER BY tick;
```

### Q2: Agent λ trajectory over time
```sql
SELECT tick, lambda_money, inventory_M 
FROM agent_snapshots 
WHERE run_id = ? AND agent_id = ? 
ORDER BY tick;
```

### Q3: Active exchange regimes by tick
```sql
SELECT tick, current_mode, exchange_regime, active_pairs 
FROM tick_states 
WHERE run_id = ? 
ORDER BY tick;
```

### Q4: Trades during specific mode/regime
```sql
SELECT t.* 
FROM trades t 
JOIN tick_states ts ON t.run_id = ts.run_id AND t.tick = ts.tick 
WHERE t.run_id = ? 
  AND ts.current_mode = 'trade' 
  AND ts.exchange_regime = 'mixed'
ORDER BY t.tick;
```

### Q5: λ convergence check (KKT mode)
```sql
SELECT agent_id, tick, lambda_old, lambda_new, clamped 
FROM lambda_updates 
WHERE run_id = ? 
ORDER BY agent_id, tick;
```

### Q6: Surplus distribution across trade types
```sql
SELECT 
    exchange_pair_type, 
    COUNT(*) as trade_count,
    AVG(buyer_surplus) as avg_buyer_surplus,
    AVG(seller_surplus) as avg_seller_surplus,
    AVG(buyer_surplus + seller_surplus) as avg_total_surplus
FROM trades 
WHERE run_id = ? 
GROUP BY exchange_pair_type;
```

---

## Implementation Checklist

- [ ] **database.py**: Add `ALTER TABLE` statements to `_create_schema()`
- [ ] **database.py**: Add `CREATE TABLE` for `tick_states` and `lambda_updates`
- [ ] **database.py**: Add indices for new columns
- [ ] **db_loggers.py**: Update `log_agent_snapshot()` to accept money params
- [ ] **db_loggers.py**: Update `log_trade()` to accept money params
- [ ] **db_loggers.py**: Add `log_tick_state()`
- [ ] **db_loggers.py**: Add `log_lambda_update()` (KKT only)
- [ ] **Test**: Run legacy scenario, verify NULL/0 defaults work
- [ ] **Test**: Run money scenario, verify money columns populate correctly
- [ ] **Docs**: Update log viewer documentation with new query capabilities

---

## Backward Compatibility Guarantee

**Legacy scenarios (no money)**:
- All new columns remain NULL or 0
- Existing queries unchanged
- Log viewer filters ignore NULL money columns
- CSV exports exclude empty money columns by default

**Mixed runs** (some with money, some without):
- Database accommodates both types
- Queries can filter by `exchange_regime` in `simulation_runs`
- Comparison views can show barter vs. money regimes side-by-side

---

## File Locations

This schema is implemented in:
- `src/telemetry/database.py` — schema definitions
- `src/telemetry/db_loggers.py` — logging methods
- `src/vmt_log_viewer/queries.py` — query templates
- `tests/test_telemetry_money.py` — schema validation tests

See also: `money_SSOT_implementation_plan.md` §9 (Telemetry and UI)

