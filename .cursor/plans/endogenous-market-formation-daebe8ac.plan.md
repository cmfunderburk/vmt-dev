<!-- daebe8ac-a7e1-49a4-8ad4-eb1ac520ca64 3112e613-89ee-45bb-a05c-b9c877c83d90 -->
# Endogenous Market Formation Implementation

## Overview

Implement a system where markets emerge organically from agent clustering rather than being pre-placed. When sufficient agents cluster within interaction range (≥5 agents), a market area forms and those agents trade via centralized Walrasian clearing. Markets persist across ticks while density remains above threshold, allowing price convergence.

## Core Design Decisions

- **Clustering:** Grid-based scanning (simple, deterministic)
- **Persistence:** Markets maintain identity across ticks with hysteresis
- **Assignment:** Exclusive (each agent in at most one market)
- **Mechanism:** Uniform Walrasian clearing for all markets
- **Identity:** Location-based (reuse ID if within 2 cells)
- **Agent Pairing:** Unpair when entering markets

## Week 1: Core Market Detection (8 hours)

### Create MarketArea dataclass

**File:** `src/vmt_engine/core/market.py` (new file)

Implement the core `MarketArea` dataclass with:

- Identity fields: `id`, `center`, `radius`
- State: `participant_ids`, `mechanism`, `current_prices`
- Lifecycle: `formation_tick`, `last_active_tick`, `ticks_below_threshold`
- Statistics: `total_trades_executed`, `total_volume_traded`, `historical_prices`

### Extend Trade Effect

**File:** `src/vmt_engine/protocols/base.py`

Add `market_id: Optional[int] = None` field to existing `Trade` effect (line 157-179):

- None = bilateral trade
- int = market trade
- Add `is_market_trade` and `is_bilateral_trade` properties

### Create Market Lifecycle Effects

**File:** `src/vmt_engine/protocols/base.py`

Add three new effect types after existing effects:

- `MarketFormation`: Logged when market forms (market_id, center, tick, num_participants)
- `MarketDissolution`: Logged when market dissolves (market_id, tick, age, reason)
- `MarketClear`: Logged after clearing (market_id, commodity, price, quantity, tick, converged)

### Implement Market Detection in TradeSystem

**File:** `src/vmt_engine/systems/trading.py`

Extend `TradeSystem` class:

- Add instance variables: `active_markets: dict[int, MarketArea]`, `next_market_id: int`
- Implement `_detect_market_areas()`: scan agents, find clusters ≥ threshold
- Implement `_find_agents_within_radius()`: Manhattan distance filtering
- Implement `_compute_cluster_center()`: geometric center calculation
- Implement `_find_or_create_market()`: location-based identity (reuse if within 2 cells)
- Implement `_update_inactive_markets()`: dissolution logic with hysteresis

**Key algorithm details:**

- Sort agents by ID for determinism
- Formation threshold: default 5 agents
- Dissolution: below 3 agents for 5 consecutive ticks
- Location tolerance: ±2 cells counts as same market

### Tests

**File:** `tests/test_endogenous_market_detection.py` (new)

Create comprehensive test suite:

- `test_market_forms_at_threshold`: 5 agents → 1 market
- `test_market_does_not_form_below_threshold`: 4 agents → 0 markets
- `test_market_persists_across_ticks`: Same ID maintained
- `test_market_dissolves_after_patience`: Low density for 5 ticks → dissolve
- `test_location_based_market_identity`: Cluster at (11,11) reuses ID from (10,10)
- `test_deterministic_market_ids`: Same seed → same market IDs

## Week 2: Market Clearing Integration (10 hours)

### Implement Agent-to-Market Assignment

**File:** `src/vmt_engine/systems/trading.py`

Add `_assign_agents_to_markets()` method:

- Exclusive assignment (one market maximum per agent)
- Priority: largest market → closest → lowest ID
- Return `dict[int, list[int]]` mapping market_id to agent_ids

### Create WalrasianAuctioneer Mechanism

**File:** `src/vmt_engine/protocols/market/walrasian.py` (new file)

Implement tatonnement-based clearing:

- `execute(market, sim)`: Main entry, clears all commodities
- `_find_clearing_price(market, commodity, sim)`: Iterative tatonnement
- `_compute_demand(market, commodity, price, sim)`: Sum agent demands
- `_compute_supply(market, commodity, price, sim)`: Sum agent supplies
- `_execute_at_price(market, commodity, price, sim)`: Match buyers/sellers

**Economic model (simplified for initial implementation):**

- Demand: buy if marginal utility > price
- Supply: sell if price > marginal utility
- Warm start from previous clearing price
- Convergence: |excess_demand| < tolerance

### Integrate Markets into TradeSystem.execute()

**File:** `src/vmt_engine/systems/trading.py`

Modify `execute()` method to add market processing before bilateral trades:

1. Detect markets (`_detect_market_areas`)
2. Assign agents (`_assign_agents_to_markets`)
3. **Unpair market participants** (clear bilateral pairing state)
4. Process market trades (call mechanism.execute)
5. Process bilateral trades (skip market participants)
6. Apply all effects

### Create Market Mechanism Factory

**File:** `src/vmt_engine/systems/trading.py`

Add `_create_mechanism()` method:

- Read `market_mechanism` param from scenario
- Instantiate `WalrasianAuctioneer` with params
- Raise `NotImplementedError` for "posted_price" and "cda" (deferred)

### Tests

**File:** `tests/test_endogenous_market_clearing.py` (new)

Market clearing tests:

- `test_market_clearing_single_commodity`: 3 buyers + 3 sellers → equilibrium
- `test_tatonnement_convergence`: Verify |excess_demand| < tolerance
- `test_tatonnement_non_convergence`: No overlap → graceful failure
- `test_warm_start`: Second clearing faster than first
- `test_market_vs_bilateral_coexistence`: 5 in market, 1 bilateral
- `test_exclusive_agent_assignment`: Overlapping markets → largest wins
- `test_unpair_on_market_entry`: Paired agents unpaired when entering market

## Week 3: Telemetry & Visualization (8 hours)

### Extend Database Schema

**File:** `src/telemetry/database.py`

Add market-specific tables in `_create_schema()`:

```sql
CREATE TABLE IF NOT EXISTS market_formations (
    market_id INTEGER,
    center_x INTEGER,
    center_y INTEGER,
    formation_tick INTEGER,
    num_participants INTEGER,
    PRIMARY KEY (market_id)
);

CREATE TABLE IF NOT EXISTS market_dissolutions (
    market_id INTEGER,
    dissolution_tick INTEGER,
    age INTEGER,
    reason TEXT,
    PRIMARY KEY (market_id, dissolution_tick)
);

CREATE TABLE IF NOT EXISTS market_clears (
    tick INTEGER,
    market_id INTEGER,
    commodity TEXT,
    clearing_price REAL,
    quantity_traded REAL,
    num_participants INTEGER,
    converged INTEGER,
    PRIMARY KEY (tick, market_id, commodity)
);

CREATE TABLE IF NOT EXISTS market_snapshots (
    tick INTEGER,
    market_id INTEGER,
    center_x INTEGER,
    center_y INTEGER,
    num_participants INTEGER,
    age INTEGER,
    total_trades INTEGER,
    PRIMARY KEY (tick, market_id)
);
```

Also add `market_id INTEGER DEFAULT NULL` to `trades` table (migration).

### Implement Telemetry Logging

**File:** `src/telemetry/db_loggers.py`

Add methods to `TelemetryManager`:

- `log_market_formation(market, tick)`: Insert into market_formations
- `log_market_dissolution(market, tick)`: Insert into market_dissolutions
- `log_market_clear(effect)`: Insert into market_clears
- `log_market_snapshot(market, tick)`: Periodic state dumps

Modify `log_trade()` to accept `market_id` parameter.

### Pygame Rendering Extensions

**File:** `src/vmt_pygame/renderer.py`

Add market visualization methods:

- `render_market_areas(screen, sim)`: Semi-transparent yellow overlays
- `render_agent_market_participation(screen, sim)`: Connection lines to market center
- Market center markers with ID labels
- Price displays at market centers

**Visual design:**

- Yellow overlay: alpha = 80 + min(100, trades * 2)
- Center marker: yellow circle, radius 8
- ID label: "M{id}" above center
- Prices: "A:1.2 B:0.8" below center

### Analysis Script

**File:** `scripts/analyze_emergent_markets.py` (new)

Create analysis script with plots:

- Market lifespan histogram (formation_tick to dissolution_tick)
- Price convergence within markets (price over time per commodity)
- Spatial market distribution heatmap
- Market count over time

### Tests

**File:** `tests/test_endogenous_market_telemetry.py` (new)

Telemetry tests:

- `test_market_formation_logged`: Verify row in market_formations
- `test_market_clearing_logged`: Verify rows in market_clears
- `test_trade_market_id_tagged`: Market trades have market_id set
- `test_bilateral_trade_untagged`: Bilateral trades have NULL market_id
- `test_market_snapshot_periodic`: Snapshots logged every N ticks

## Week 4: Scenarios & Refinement (6 hours)

### Create Demonstration Scenarios

**Directory:** `scenarios/demos/`

Create three YAML scenarios:

**`emergent_market_basic.yaml`:**

- Single resource cluster at (20, 20)
- 20 agents, Cobb-Douglas utility
- Expect: Market forms at resource cluster

**`emergent_market_multi.yaml`:**

- Two resource clusters: A at (10,10), B at (30,30)
- 30 agents
- Expect: Two markets form, different prices initially

**`emergent_market_nomadic.yaml`:**

- Resources regenerate slowly
- Agents migrate between depleted and fresh clusters
- Expect: Markets form, dissolve, reform at new locations

**Parameters in all scenarios:**

```yaml
market_formation_threshold: 5
market_dissolution_threshold: 3
market_dissolution_patience: 5
market_mechanism: "walrasian"
walrasian_adjustment_speed: 0.1
walrasian_tolerance: 0.01
walrasian_max_iterations: 100
```

### Update Scenario Loader

**File:** `src/scenarios/loader.py`

Extend `load_scenario()` to extract market parameters from YAML:

- `market_formation_threshold` (default: 5)
- `market_dissolution_threshold` (default: 3)
- `market_dissolution_patience` (default: 5)
- `market_mechanism` (default: "walrasian")
- Walrasian parameters (adjustment_speed, tolerance, max_iterations)

### Documentation Updates

**Files:** `docs/2_technical_manual.md`, `README.md`

Add sections:

- Endogenous Markets overview
- Market formation conditions
- Configuration parameters
- Pedagogical use cases
- Comparison with pre-defined markets

### Scenario Tests

**File:** `tests/test_endogenous_market_scenarios.py` (new)

High-level scenario tests:

- `test_market_at_resource_cluster`: Market forms near resources
- `test_multiple_markets_coexist`: Two clusters → two markets
- `test_price_convergence_over_time`: Variance decreases
- `test_efficiency_gain_vs_bilateral`: Market scenario > bilateral-only

### Determinism Verification

**Script:** Run existing `scripts/compare_telemetry_snapshots.py`

Verify determinism:

```bash
bash -c "source venv/bin/activate && python scripts/compare_telemetry_snapshots.py scenarios/demos/emergent_market_basic.yaml --seed 42 --runs 2"
```

Assert: Byte-for-byte identical telemetry databases.

## Key Implementation Details

### Determinism Requirements

- Agent scanning: `sorted(sim.agents, key=lambda a: a.id)`
- Market processing: `sorted(markets, key=lambda m: m.id)`
- Assignment priority: deterministic tie-breaking
- No unseeded randomness in tatonnement

### Agent/Inventory API

- Access inventory: `agent.inventory.A`, `agent.inventory.B`, `agent.inventory.M`
- Marginal utility: `agent.utility.mu_A(A, B)`, `agent.utility.mu_B(A, B)`
- Money MU: `agent.lambda_money`

### Phase 2 Interaction (Future Enhancement)

Current: Agents unpaired when entering markets (Step 3 of Phase 4)

Future: Modify MatchingProtocol to skip pairing in high-density areas

### Performance Note

Performance optimization is **not a priority** during initial implementation. Focus on correctness first. Optimization deferred to post-verification phase.

## Success Criteria

**Week 1 Complete:**

- Markets form at density threshold
- Markets dissolve after patience period
- Location-based identity works
- Console logs show lifecycle events

**Week 2 Complete:**

- Walrasian mechanism clears markets
- Market and bilateral trades coexist
- Tatonnement converges reliably
- Trade effects tagged with market_id

**Week 3 Complete:**

- Telemetry captures all market events
- Pygame displays market areas
- Analysis script generates plots
- Price convergence observable

**Week 4 Complete:**

- Demonstration scenarios run
- Documentation updated
- Markets form at expected locations
- Efficiency gains measurable

**Overall Success:**

- Determinism verified (same seed → identical results)
- Markets emerge at natural gathering points
- Ready for classroom use

### To-dos

- [ ] Create MarketArea dataclass in src/vmt_engine/core/market.py
- [ ] Add market_id field to Trade effect in protocols/base.py
- [ ] Create MarketFormation, MarketDissolution, MarketClear effects
- [ ] Implement market detection methods in TradeSystem
- [ ] Create test_endogenous_market_detection.py with 6+ tests
- [ ] Implement _assign_agents_to_markets() with priority logic
- [ ] Create WalrasianAuctioneer in protocols/market/walrasian.py
- [ ] Modify TradeSystem.execute() to process markets before bilateral
- [ ] Create test_endogenous_market_clearing.py with 7+ tests
- [ ] Add market tables to database.py schema
- [ ] Implement market logging methods in db_loggers.py
- [ ] Add market rendering to pygame renderer
- [ ] Create scripts/analyze_emergent_markets.py
- [ ] Create test_endogenous_market_telemetry.py
- [ ] Create 3 demo scenarios (basic, multi, nomadic)
- [ ] Update scenario loader to parse market parameters
- [ ] Update technical manual and README
- [ ] Create test_endogenous_market_scenarios.py
- [ ] Verify determinism with compare_telemetry_snapshots.py