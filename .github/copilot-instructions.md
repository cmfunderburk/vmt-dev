# Copilot Instructions for VMT (Visualizing Microeconomic Theory)

## Project Overview

VMT is a **Python-only desktop application** for simulating microeconomic behavior through grid-based agent interactions. Built on **Pygame** with a deterministic, delta-based engine running at 10 Hz (configurable) and rendering at 60 FPS.

## Core Architecture Principles

### 1. Decoupled Engine & Renderer
- **`vmt_engine/`**: UI-agnostic simulation logic (agents, grid, utilities, matching, deltas)
- **`vmt_pygame/`**: Event loop, rendering, HUD, and input handling
- **Never mix engine state mutations with Pygame rendering code**

### 2. Delta-Based Simulation Contract
All state changes flow through a strict delta system:

```python
# Engine API (vmt_engine/core/)
initialize_state(params) -> dict          # Creates immutable initial state
step(state, dt) -> list[delta]            # Pure function, NO mutations
apply_delta(state, deltas) -> None        # Single mutation point
analytics(state) -> dict                  # Optional metrics
```

**Delta vocabulary** (see Planning.md §2.2):
- Movement: `{"op":"move","id":i,"to":[x,y]}`
- Harvest/Deposit: `{"op":"harvest"|"deposit","id":i,"cell":[x,y],"resource":"A","d":float}`
- Trades: `{"op":"trade","i":i,"j":j,"give":{...},"take":{...}}`
- Offers: `{"op":"post_offer"|"retract_offer","cell":[x,y],...}`

**Critical**: Never mutate state directly in step() functions. Always return deltas.

### 3. Five-Stage Step Pipeline
Each simulation tick follows this rigid sequence (§2.3):
1. **Perception**: Agents scan neighborhoods (resources, offers, neighbors, price signals)
2. **Decision**: Generate movement intents, barter proposals, or order postings
3. **Matching**: Execute barter/cash trades based on mode
4. **Transitions**: Craft deltas for all state changes
5. **Apply & Housekeeping**: Apply deltas, update utilities/beliefs, emit telemetry

## State Schema (Grid-First Design)

Reference `Planning.md §2.1` for the canonical state structure. Key points:

- **Grid**: N×N cells (default 32×32), each with resources and optional posted offers
- **Agents**: Position `[x,y]`, inventory `{"A":float, "B":float, "$":float}`, traits, policies, beliefs
- **Modes**: 
  - `exchange_mode="barter"`: Integer bundle trades, ΔU>0 for both parties
  - `exchange_mode="cash"`: Per-cell order books with lot sizes and tick prices

## Technology Stack Requirements

- **Runtime**: Python 3.11+
- **Core Dependencies**: Pygame, NumPy (required)
- **Optional**: Numba (hot paths), Matplotlib (post-run analysis)
- **Packaging**: PyInstaller for Win/macOS

When adding dependencies, update `pyproject.toml` with pinned versions.

## Scenario Presets (Configuration over Code)

Three educational modules share one engine, controlled by behavior toggles (§3):

1. **Foraging**: `foraging=True`, trading off → spatial resource gathering
2. **Bilateral Exchange**: `exchange_mode="barter"`, `search_trade=True` → integer bundle trades
3. **Market Clearing**: `exchange_mode="cash"`, `post_offers=True` → per-cell order books

**Never create separate model classes per scenario**. Use parameter configurations in `vmt_engine/presets/`.

## Utility Functions

Support **six utility types** (§2.3, Open Decision #3):
- **Cobb-Douglas** (v1 must-have)
- **CES** (v1 must-have)
- **Leontief** (v1 must-have)
- **Linear** (v1 must-have)
- **Stone-Geary (LES)** (confirm for v1)
- **Quasi-linear** (confirm for v1)

Implement in `vmt_engine/econ/utility.py` with a **registry pattern**. MRS calculation must work for multi-good cases in barter mode.

## Testing & Validation Standards

Write tests for (`tests/`):
- **Conservation laws**: Total inventory preserved across trades
- **ΔU>0 acceptance**: Both parties improve utility in barter
- **Integer invariants**: Barter uses integer lots only
- **Determinism**: Same seed → same outcome
- **Matcher fairness**: FIFO within price levels (cash mode)

Use fixed `rng_seed` values in all tests for reproducibility.

## Critical Constraints

### Barter Mode (Open Decision #1)
- Trades use **integer lots only** (e.g., `{"A":2, "B":1}`)
- Goods are integers; money `$` is float
- Max lots per tick (configurable)
- Acceptance requires **mutual ΔU>0**

### Cash Mode (Open Decision #2)
- Orders posted with `lot_size` (integer) and `cash_tick_size` (float, e.g., 0.1)
- Per-cell "bulletin board" matcher crossing bids/asks
- Price signals updated on fills (last trade price)
- TTL (time-to-live) for order expiration

### Performance Targets
- 10 Hz simulation default (5–60 Hz configurable)
- 60 FPS rendering
- Support 50–100 agents initially; scale with Numba if needed
- Deterministic fixed-timestep accumulator pattern

## File Organization Conventions

```
vmt_engine/
  core/         # state.py, grid.py, agent.py, delta.py
  econ/         # utility.py (registry), pricing.py
  systems/      # perception.py, decision.py, matching.py, transitions.py, housekeeping.py
  models/       # base.py (BaseSimulationModel)
  presets/      # foraging.py, exchange.py, market.py

vmt_pygame/
  app.py        # Main loop, sim_dt control, pause/reset/speed
  renderers.py  # Grid/agents/overlays/HUD
  input.py      # Hotkeys, preset picker

scripts/        # run_pygame.py, export_run.py
tests/          # Engine + matcher + utility suites
```

Keep engine code in `vmt_engine/` completely independent of Pygame imports.

## Development Workflow

1. **Run app**: `python scripts/run_pygame.py`
2. **Tests**: Standard pytest in `tests/`
3. **Logging**: CSV exports every N ticks for analysis
4. **Hotkeys**: Space (pause/resume), R (reset), 1/2 (speed), Esc (quit)

## Milestones (See Planning.md)

- **M1 (Week 1)**: Engine skeleton + Pygame loop + Foraging preset
- **M2 (Week 2)**: Barter mode with integer bundles
- **M3 (Week 3)**: Cash mode with order books
- **M4 (Week 4)**: Polish, packaging, teacher notes

## References

All architectural details, open decisions, and rationale documented in `Planning.md`. Consult sections:
- §1: Architecture patterns
- §2: Engine design & delta vocabulary
- §3: Scenario presets
- §4: Pygame UX
- "Open Decision Points": Unresolved design choices requiring discussion before implementation
