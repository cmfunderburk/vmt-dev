# VMT (Visualizing Microeconomic Theory) - AI Agent Instructions

## Project Identity
**VMT** is a spatial agent-based simulation for teaching and researching microeconomic behavior through visualization. Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral trade (barter or monetary exchange) using reservation-price-based negotiation.

**Tech Stack:** Python 3.11+, PyQt6 (GUI), PyGame (visualization), SQLite (telemetry), NumPy

## Critical Architecture: 7-Phase Deterministic Engine

The simulation runs in a **strict 7-phase tick cycle** (defined in `src/vmt_engine/simulation.py`):

1. **Perception** - Frozen snapshot of world state (neighbors, quotes, resources)
2. **Decision** - Three-pass pairing algorithm with money-aware surplus calculation
3. **Movement** - Manhattan movement toward targets with deterministic tie-breaking
4. **Trade** - Only paired agents within interaction_radius attempt trades
5. **Forage** - Unpaired agents harvest resources (paired agents skip)
6. **Regeneration** - Resource cells regenerate over time
7. **Housekeeping** - Quote refresh, pairing integrity checks, telemetry logging

**NEVER** change this phase order or phase boundaries. Determinism depends on it.

## Core Determinism Rules (Non-Negotiable)

- **Sorted Iteration:** Always process agents by `agent.id`. Always process trade pairs by `(min_id, max_id)`. Use `sorted()` explicitly.
- **Fixed Tie-Breaking:** Movement prefers x-axis before y-axis, negative direction on ties. Diagonal deadlock resolved by higher ID.
- **Frozen Quotes:** Quotes computed in Housekeeping only. Set `agent.inventory_changed = True` to flag for refresh.
- **Pairing Commitment:** Once paired, agents are exclusive until trade fails or mode changes. No re-evaluation mid-pairing.
- **Round-Half-Up:** For price→quantity mapping, use `floor(price * ΔA + 0.5)` to ensure deterministic rounding.
- **Same Seed → Identical Output:** This is the most important guarantee. Test all changes with fixed seeds.

## Money System (Phase B Complete)

**Quasilinear Utility:** `U_total = U_goods(A, B) + λ·M` where λ is agent-specific marginal utility of money.

**Exchange Regimes** (in `src/scenarios/schema.py`):
- `barter_only` - Only A↔B trades (uses legacy `compute_surplus()`)
- `money_only` - Only A↔M, B↔M trades
- `mixed` - All trade types allowed (A↔M > B↔M > A↔B priority on equal surplus)

**Money-Aware Pairing:** In `money_only`/`mixed` regimes, use `estimate_money_aware_surplus()` (in `src/vmt_engine/systems/matching.py`). This uses quote overlaps as a heuristic proxy for utility gains (performance trade-off: O(1) vs O(dA_max × prices) for exact calculation).

**Important:** Money holdings (M) are stored in **minor units** (e.g., cents). Use `money_scale` parameter for conversion.

## Key System Files

- **Core Engine:** `src/vmt_engine/simulation.py` - Main simulation loop
- **Decision Logic:** `src/vmt_engine/systems/decision.py` - Three-pass pairing algorithm (MONOLITHIC, needs refactoring)
- **Trading System:** `src/vmt_engine/systems/trading.py` - Trade execution with compensating block search
- **Matching Logic:** `src/vmt_engine/systems/matching.py` - Surplus calculation and exchange pair selection
- **Utility Functions:** `src/vmt_engine/econ/utility.py` - 5 utility types (CES, Linear, Quadratic, Translog, Stone-Geary)
- **Scenario Schema:** `src/scenarios/schema.py` - YAML configuration structure
- **Scenario Loader:** `src/scenarios/loader.py` - Parses YAML into simulation objects

## Utility Functions (All in `src/vmt_engine/econ/utility.py`)

1. **CES** - Constant Elasticity of Substitution (includes Cobb-Douglas when ρ→0)
2. **Linear** - Perfect substitutes with constant MRS
3. **Quadratic** - Bliss points with satiation (non-monotonic)
4. **Translog** - Flexible second-order approximation for empirical work
5. **Stone-Geary** - Subsistence constraints (γ_A, γ_B); requires initial inventory > subsistence

**Zero-Inventory Guard:** When inventory is zero, add epsilon to ratio calculation for MRS only. Never modify core `u_goods(A, B)` calculation.

## Testing Strategy

**316+ tests** in `tests/` directory. Run with `pytest` from project root.

**Key Test Categories:**
- **Money Integration:** `test_money_phase1_integration.py`, `test_pairing_money_aware.py`
- **Barter Regression:** `test_barter_integration.py` - Ensures bit-identical backward compatibility
- **Mixed Regime:** `test_mixed_regime_integration.py`, `test_mixed_regime_tie_breaking.py`
- **Performance:** `test_performance.py`, `test_performance_scenarios.py`

**When adding features:**
1. Write tests for new behavior
2. Run full test suite to ensure determinism preserved
3. Check `test_barter_integration.py` specifically for backward compatibility

## Development Workflow

**Entry Points:**
- GUI: `python launcher.py` (PyQt6 scenario browser)
- CLI: `python main.py scenarios/demo.yaml --seed 42`
- Headless: `python scripts/run_headless.py`

**Code Quality:**
- Formatting: Black (run `black .`)
- Linting: Ruff (run `ruff check .`)
- Type Checking: Mypy (goal: 100% type coverage)

**Python Path:** `sys.path.insert(0, 'src')` in main entry points. Tests use `pytest.ini` pythonpath setting.

## Telemetry System

**SQLite Logging:** All simulation data logged to `logs/telemetry_<timestamp>.db` (99% compression over CSV).

**Key Tables:**
- `runs` - Simulation metadata
- `agent_snapshots` - Per-tick agent state (position, inventory, quotes)
- `trades` - Individual trade events with prices and quantities
- `preferences` - Agent preference rankings with pair_type
- `pairing_events` - Pair formation/dissolution

**Log Viewer:** `python -m src.vmt_log_viewer.main` or use launcher GUI.

## Current Development Context (Updated 2025-01-27)

**Completed:** Phase A (Foraging & Barter) + Phase B (Money System) are production-ready.

**Next Priority:** Protocol Modularization Refactor (2-3 months) before Phase C (Market Mechanisms).

**Critical Issue:** `DecisionSystem` is monolithic and tightly coupled. Cannot add advanced market mechanisms (posted-price, auctions) without refactoring. Need to extract search and matching logic into `SearchProtocol` and `MatchingProtocol` interfaces.

**Blocked Features:**
- KKT Lambda Mode (endogenous λ estimation)
- Mixed Liquidity Gated (barter fallback when money market thin)
- Phase C Market Mechanisms (posted-price markets, auctions)

## Project Conventions

**Versioning:** No SemVer until developer manually pushes 0.0.1 prerelease. Use date-based tracking in commit messages.

**Type Safety:** All code uses type hints. Inventories (A, B, M), resources, positions are `int`. Utility values, prices, λ are `float`.

**Scenario Files:** YAML format in `scenarios/` directory. See `docs/scenario_configuration_guide.md` for parameter reference.

**Documentation:** 
- `docs/1_project_overview.md` - Complete feature overview
- `docs/2_technical_manual.md` - Implementation details
- `docs/3_strategic_roadmap.md` - Development priorities
- `docs/structures/` - Parameter quick reference tables

## Common Pitfalls to Avoid

1. **Don't iterate over dicts for side effects** - Use sorted agent lists
2. **Don't mutate quotes mid-tick** - Only in Housekeeping phase
3. **Don't skip epsilon guards** - Zero inventories break MRS calculation
4. **Don't change phase order** - Ever. Even for "optimization."
5. **Don't forget inventory_changed flag** - Quotes won't refresh otherwise
6. **Don't mix integer/float types** - Goods are int, prices are float
7. **Don't add features without tests** - Especially determinism tests

## Quick Reference: Adding a New Feature

1. **Read relevant docs** - Start with `docs/2_technical_manual.md`
2. **Identify phase** - Which of the 7 phases does your feature belong to?
3. **Check exchange regime** - Does it work for barter/money/mixed?
4. **Preserve determinism** - Use sorted iteration, fixed tie-breaking
5. **Write tests first** - Include determinism validation
6. **Update schema** - If adding YAML parameters, update `src/scenarios/schema.py`
7. **Run full test suite** - Ensure backward compatibility
8. **Update docs** - Especially parameter reference if adding config options

## Example: Money-Aware Pairing Decision

```python
# In Decision phase, when selecting exchange pair:
if exchange_regime in ["money_only", "mixed"]:
    # Use money-aware surplus calculation
    surplus, pair_type = estimate_money_aware_surplus(
        agent_i, agent_j, exchange_regime
    )
    # pair_type is "A_for_M", "B_for_M", or "A_for_B"
else:  # barter_only
    # Use legacy barter surplus for backward compatibility
    surplus = compute_surplus(agent_i, agent_j)
    pair_type = "A_for_B"
```

## When You Need Help

- **Architecture questions:** Read `src/vmt_engine/README.md` and `.cursor/rules/vmt-7-phase-engine.mdc`
- **Economic models:** See `.cursor/rules/vmt-economic-models.mdc` and `src/vmt_engine/econ/utility.py`
- **Scenario configuration:** Check `docs/scenario_configuration_guide.md` and `.cursor/rules/vmt-scenarios-config.mdc`
- **Testing patterns:** Look at existing tests in `tests/` and `.cursor/rules/vmt-testing-quality.mdc`
