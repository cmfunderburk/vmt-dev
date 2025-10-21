# VMT (Visualizing Microeconomic Theory) - AI Agent Instructions

## Project Overview

VMT is a **spatial agent-based simulation for teaching microeconomics** through interactive visualization. Agents with heterogeneous preferences forage resources and engage in bilateral trade (barter or monetary exchange) on a grid-based world. This is a **pedagogical research tool** focused on determinism, reproducibility, and economic theory accuracy.

**Key Characteristics:**
- Python 3.11+ with PyQt5 (GUI launcher), Pygame (visualization), SQLite (telemetry)
- 316+ tests emphasizing determinism and economic correctness
- Pre-release status: Use date-based identifiers (e.g., `2025-10-21`), NOT SemVer versions
- Entry points: `launcher.py` (GUI), `main.py` (CLI), `view_logs.py` (telemetry viewer)

## Architecture: The 7-Phase Tick Cycle

The simulation engine (`src/vmt_engine/simulation.py`) orchestrates a **strict 7-phase cycle** executed each tick in deterministic order:

1. **Perception** → Agents observe environment (frozen snapshot)
2. **Decision** → Three-pass pairing algorithm builds preferences and establishes partnerships
3. **Movement** → Agents move toward targets (paired partner, resource, or position)
4. **Trading** → Only paired agents within `interaction_radius` attempt trades
5. **Foraging** → Agents harvest resources (paired agents skip)
6. **Resource Regeneration** → Resources regrow based on cooldown/growth rate
7. **Housekeeping** → Quote refresh, pairing integrity checks, lambda updates, telemetry logging

**Critical Invariant:** All agent loops iterate in sorted ID order (`sorted(sim.agents, key=lambda a: a.id)`) for determinism.

## Economic Systems Deep Dive

### Utility Functions (5 types in `src/vmt_engine/econ/utility.py`)
- `UCES`: Constant Elasticity of Substitution (includes Cobb-Douglas as special case)
- `ULinear`: Perfect substitutes
- `UQuadratic`: Bliss points and satiation
- `UTranslog`: Transcendental logarithmic (flexible second-order)
- `UStoneGeary`: Subsistence constraints (LES foundation)

**Money-Aware API Pattern:**
```python
u_goods(A, B)      # Utility from goods only (canonical)
mu_A(A, B)         # Marginal utility of good A (∂U/∂A)
u_total(inv, params)  # Total utility including money (Phase 3+)
```

**Zero-Inventory Guard:** CES utilities add tiny `epsilon` to inventories *only* for MRS ratio calculations in `reservation_bounds_A_in_B()`. Core `u_goods(A, B)` always uses true integer inventories.

### Exchange Regimes & Money System (Phase 1+)
Four regimes defined in scenario YAML (`src/scenarios/schema.py`):
- `barter_only`: Only A↔B trades allowed
- `money_only`: Only A↔M and B↔M trades allowed
- `mixed`: All three types (A↔B, A↔M, B↔M) allowed with **money-first tie-breaking**
- `mixed_liquidity_gated`: Mixed + liquidity constraints (Track 2, partially implemented)

**Money-First Tie-Breaking:** In `mixed` regimes, when multiple trade types have equal surplus, monetary trades (A↔M, B↔M) are preferred over barter (A↔B). See `_rank_trade_candidates()` in `src/vmt_engine/systems/trading.py`.

**Quasilinear Utility:** U_total = U_goods(A, B) + λ·M, where λ is marginal utility of money, M is money in minor units.

### Mode Schedule (Temporal Control)
`mode_schedule` in scenario YAML controls **when** systems run:
- `forage` mode: Skip TradeSystem entirely (zero trade attempts)
- `trade` mode: Skip ForageSystem
- `both` mode: Run all systems
- Mode changes trigger automatic unpairing (no cooldown penalty)

**vs. Exchange Regime:** Mode schedule controls WHEN (temporal), regime controls WHAT types of trades (A↔B vs A↔M vs B↔M).

## Critical Developer Workflows

### Running Tests
```bash
# All tests (requires pythonpath in pytest.ini)
pytest

# Specific test file
pytest tests/test_money_phase1.py -v

# Determinism check (same seed → identical logs)
pytest tests/test_money_phase1_integration.py::test_determinism -v
```

### Running Simulations
```bash
# GUI launcher (recommended)
python launcher.py

# CLI with visualization
python main.py scenarios/three_agent_barter.yaml 42

# CLI with money system demo
python main.py scenarios/demos/demo_01_simple_money.yaml --seed 42

# Headless for performance benchmarking
python scripts/run_headless.py scenarios/perf_both_modes.yaml --ticks 1000
```

### Telemetry & Analysis
```bash
# View simulation logs (GUI)
python view_logs.py

# Export CSV from specific run
python view_logs.py --export run_2025-10-21_143045.db

# Analyze trade distribution
python scripts/analyze_trade_distribution.py logs/baseline_telemetry.db
```

## Project-Specific Conventions

### Pairing System (Decision Phase)
**Three-Pass Algorithm** (`src/vmt_engine/systems/decision.py`):
1. **Pass 1:** All agents build ranked preference lists using **distance-discounted surplus** = `surplus × β^distance` (Manhattan)
2. **Pass 2:** Mutual consent pairing for agents who list each other as top choice (lower ID executes pairing)
3. **Pass 3:** Best-available fallback using greedy matching on sorted potential pairs

**Commitment Semantics:** Once paired, agents maintain exclusive partnership until:
- Trade fails (no mutually beneficial terms found)
- Mode changes from `trade`/`both` to `forage`
- Pairing corruption detected (defensive integrity checks in Housekeeping)

**Trade Cooldown:** Failed trades trigger mutual cooldown (`trade_cooldown_ticks`), preventing futile re-targeting.

### Resource Claiming System
When `enable_resource_claiming=True` (default):
- Agents "claim" forage targets in `sim.resource_claims` dict to reduce clustering
- Claims cleared at start of each tick (Pass 1 of Decision phase)
- Foraging commitment maintained if resource still exists

### Telemetry Invariants
**Critical Rules** (see `.cursor/rules/telemetry-and-tests.mdc`):
- Do NOT mutate quotes mid-tick; refresh only in Housekeeping phase
- Log `exchange_pair_type` ("A<->B", "A<->M", "B<->M") for all trades in money-aware regimes
- Pairing integrity: Detect and repair asymmetric pairings; log unpair events with reason
- Mode changes: Log `(tick, old_mode -> new_mode)` and clear pairings without cooldown

**Database Schema:** See `baseline_schema.sql` for full SQLite schema. Key tables:
- `agent_snapshots`: Per-tick agent state (pos, inventory, lambda, pairing)
- `trade_events`: All executed trades with `exchange_pair_type`, `buyer_lambda`, `seller_lambda`, `dM`
- `pairing_events`: Pair/unpair events with reasons
- `tick_states`: Per-tick aggregates and mode information

### Determinism Enforcement
**Non-Negotiable Rules:**
1. All agent loops use `sorted(sim.agents, key=lambda a: a.id)`
2. Potential trade pairs sorted by `(min_id, max_id)` before greedy matching
3. Tie-breaking in movement: x-axis before y-axis, negative direction on ties
4. Same seed → identical RNG sequence (numpy PCG64)
5. No reliance on dict iteration order (use sorted keys)

**Testing:** Every behavioral change must preserve determinism tests (e.g., `test_money_phase1_integration.py::test_determinism`).

### Money-Aware Pairing (Track 2, Planned)
**Current State:** Decision phase uses barter-only surplus (`compute_surplus()` in `src/vmt_engine/systems/matching.py`) for neighbor ranking, while trading phase is money-aware (`find_best_trade()`, `find_all_feasible_trades()`).

**Guidelines for Future Work** (see `.cursor/rules/money-aware-pairing.mdc`):
- When `exchange_regime` ∈ {"money_only", "mixed"}, prefer money-aware neighbor scores
- Maintain determinism: Sort candidates by `(-score, partner_id)`
- Avoid mid-tick quote mutation; use snapshot from Perception
- Performance: Lightweight estimator or cap attempts to avoid O(N²) scans
- Acceptance: Barter-only scenarios remain bit-identical

## Integration Points

### Scenario Schema (`src/scenarios/schema.py`)
Scenarios are YAML files defining:
- `N`: Grid size (square grid)
- `agents`: Number of agents
- `initial_inventories`: Dict with keys `A`, `B`, `M` (int or list)
- `utilities.mix`: List of `{type, weight, params}` for heterogeneous populations
- `params`: Simulation parameters (vision_radius, dA_max, exchange_regime, etc.)
- `mode_schedule`: Optional temporal control (forage/trade/both cycles)
- `resource_seed`: Resource density and initial amounts

**Loader:** `src/scenarios/loader.py` validates and instantiates `ScenarioConfig`.

### GUI Components
- **Launcher** (`src/vmt_launcher/`): PyQt5 app for browsing/creating scenarios, launching simulations
- **Renderer** (`src/vmt_pygame/renderer.py`): Pygame visualization with keyboard controls (Space=pause, M=money labels, L=lambda heatmap, I=mode/regime overlay)
- **Log Viewer** (`src/vmt_log_viewer/`): PyQt5 app for querying telemetry database, CSV export, trade distribution analysis

### External Dependencies
- `numpy`: RNG (PCG64), distance calculations
- `pygame`: Visualization and keyboard input
- `PyQt5`: GUI launcher and log viewer
- `sqlite3`: Telemetry database (built-in)
- `pytest`: Test framework
- `pyyaml`: Scenario file parsing

## Common Pitfalls

1. **Breaking Determinism:** Adding any `random.choice()`, `set()` iteration, or unsortered agent loops. Always use `sim.rng` and sort by ID.
2. **Mid-Tick Quote Mutation:** Quotes MUST only refresh in Housekeeping phase. Never call `compute_quotes()` in Perception/Decision/Trading.
3. **Pairing Asymmetry:** If modifying pairing logic, ensure both agents' `paired_with_id` are set atomically. Housekeeping has defensive checks.
4. **Zero-Inventory MRS:** When adding utility functions, implement `reservation_bounds_A_in_B()` with epsilon guard for zero inventories (see UCES example).
5. **Money vs Barter Confusion:** `exchange_regime` determines allowed trade types; `mode_schedule` determines when trading happens at all.

## Key Files Reference

- **Core Loop:** `src/vmt_engine/simulation.py`
- **Systems:** `src/vmt_engine/systems/{perception,decision,movement,trading,foraging,housekeeping}.py`
- **Utilities:** `src/vmt_engine/econ/utility.py`
- **Matching Logic:** `src/vmt_engine/systems/matching.py` (surplus, feasibility, execution)
- **Scenario Schema:** `src/scenarios/schema.py`, `src/scenarios/loader.py`
- **Telemetry:** `src/telemetry/database.py`, `src/telemetry/db_loggers.py`
- **Tests:** `tests/test_money_phase*.py`, `tests/test_mixed_regime*.py`, `tests/test_mode_*.py`
- **Docs:** `docs/1_project_overview.md`, `docs/2_technical_manual.md`, `docs/4_typing_overview.md`

## Documentation & Versioning

- **Versioning Policy:** Pre-release, no SemVer. Use date+time identifiers (e.g., `2025-10-21-1430`) for snapshots.
- **Changelog:** Maintain `CHANGELOG.md` using Keep a Changelog format.
- **Docs Hygiene:** Broken links in README (e.g., `docs/user_guide_money.md`) should be stubbed with `[PLANNED]` status if not implemented.
- **Badges:** Align with pre-release status; avoid conflicting version claims.

## Testing Strategy

- **Unit Tests:** Individual system behaviors (e.g., `test_utility_ces.py`, `test_matching_money.py`)
- **Integration Tests:** Full tick cycle with specific scenarios (e.g., `test_money_phase1_integration.py`)
- **Determinism Tests:** Same seed produces identical telemetry logs
- **Performance Tests:** Benchmark scenarios in `scenarios/perf_*.yaml` for O(N) scaling validation
- **Pedagogical Tests:** Verify economic correctness (e.g., money-first tie-breaking, reservation pricing)

**Target:** All tests must pass before merging. New features require accompanying determinism test.
