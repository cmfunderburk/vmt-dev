# Session Re-Entry: Protocol Modularization Initiative

**Date Created:** 2025-10-25  
**Status:** Pre-implementation design review complete  
**Next Action:** Decision point on implementation approach

---

## Executive Summary

You are at a critical architectural decision point for VMT. The current monolithic `DecisionSystem` must be refactored to support Phase C market mechanisms (posted-price markets, auctions, alternating-offer bargaining). A comprehensive protocol modularization proposal has been reviewed and is ready for implementation planning.

**Key Insight:** The 7-phase simulation loop can be decomposed into protocol seams with strict contracts, enabling swappable market mechanisms while preserving determinism and backward compatibility.

---

## What You Were Doing

### Primary Task
Reviewing a formal protocol modularization architecture proposal in:
- **File:** `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/docs/proposals/quickreview.md`
- **Purpose:** Transform VMT's monolithic decision/trading system into a modular protocol architecture
- **Motivation:** Current architecture cannot support advanced market mechanisms needed for Phase C

### Context
- **P0 Money-Aware Pairing:** Recently completed (2025-10-22)
- **Current State:** 316+ tests passing, deterministic engine working
- **Blocker:** Need architectural refactor before implementing Phase C features
- **Timeline:** 2-3 month refactoring effort estimated

---

## Key Architectural Proposal (from quickreview.md)

### Core Principle
**"Pure inputs → explicit effects"** with simulation core as sole state mutator.

Every protocol receives:
- **Input:** Frozen `WorldView` snapshot (read-only)
- **Output:** List of `Effect` objects (declarative intents)

### The 7 Phases Decomposed

1. **Perception** (Core Service)
   - Builds deterministic `WorldView` per agent
   - No protocol hook - pure infrastructure

2. **Decision** (Split into two protocols)
   - `SearchProtocol`: Choose targets (partner/resource/position)
   - `MatchingProtocol`: Given preferences, emit `Pair` effects

3. **Movement** (Optional Policy)
   - `MovementPolicy`: Given target, emit `Move` effects

4. **Trade** (Swappable Protocol)
   - `BargainingProtocol`: Given matched pair, emit `Trade` or `Unpair` effects
   - Supports single-tick and multi-tick bargaining

5. **Foraging** (Optional Policy)
   - `ForagingPolicy`: Emit `Harvest` effects

6. **Resource Regeneration** (Core Service)
   - Pure mechanics, no protocol needed (unless ecological plugins desired)

7. **Housekeeping** (Optional Policy)
   - `HousekeepingPolicy`: Integrity checks, quote refresh, cooldown management

### Effect Types (Declarative Intents)

```python
SetTarget(agent_id, {pos|agent_id|resource_id})
ClaimResource(agent_id, pos) / ReleaseClaim(pos)
Pair(a_id, b_id, reason) / Unpair(a_id, b_id, reason)
Move(agent_id, dx, dy)
Trade(buyer_id, seller_id, pair_type, dA, dB, dM, price, meta)
Harvest(agent_id, pos, amount)
RefreshQuotes(agent_id) / SetCooldown(a,b,ticks)
InternalStateUpdate(protocol_name, agent_id, key, value)  # For multi-tick state
```

**Critical:** Only the simulation core validates, applies, and logs effects.

---

## Why This Matters (Economic Theory Connection)

### Current Limitation
The monolithic `DecisionSystem` hard-codes:
- Distance-discounted surplus search
- Three-pass pairing algorithm
- First-acceptable-trade bargaining with compensating blocks

### What You Cannot Currently Model
- **Rubinstein alternating offers** (multi-period bargaining with discounting)
- **Nash/Kalai-Smorodinsky bargaining solutions** (axiomatic approaches)
- **Posted-price markets** (Walrasian mechanisms)
- **Auctions** (sealed-bid, ascending, Dutch)
- **Search with memory** (price learning, spatial heterogeneity)
- **Take-it-or-leave-it offers** (monopoly power analysis)

### What This Architecture Enables
Each protocol implements a testable economic hypothesis:
- **Comparative institutional analysis:** Run same scenario with different bargaining protocols
- **Mechanism design experiments:** Test protocol performance metrics
- **Robustness checks:** Verify theoretical predictions across implementations
- **Publication-quality results:** Telemetry tracks exact protocol version used

---

## Determinism Guarantees (Non-Negotiable)

### Core Rules
1. **Sorted iteration:** All agent loops by ascending `agent.id`
2. **Fixed effect application order:** Documented per phase
3. **RNG discipline:** Per-protocol streams by (agent_id, tick)
4. **No shared state:** Protocols get snapshots, return effects only

### Testing Strategy
- **Golden reproduction:** Same seed → identical outcomes across protocol versions
- **Cross-protocol invariants:** Verify claimed properties (symmetry, Pareto efficiency)
- **Property-based tests:** Monotone utilities, finite reservation prices, ΔU > 0
- **Performance bounds:** Document O() complexity per protocol

---

## Telemetry Extensions Required

### New Tables
```sql
protocol_runs(
  run_id, tick, simulation_type,
  search_name@version,
  matching_name@version,
  bargaining_name@version,
  movement_name@version,
  foraging_name@version
)

protocol_events(
  run_id, tick, protocol, kind,
  agent_id, pair, payload_json
)

bargaining_states(
  run_id, tick, pair,
  state_key, state_val
)
```

### Schema Updates
Add `protocol_version` columns to:
- `pairings`
- `preferences`
- `trade_attempts`
- `trades`

**Purpose:** Reproducibility and cross-protocol comparison.

---

## Proposed Scenario Configuration

```yaml
protocols:
  search:
    name: "distance_discounted"
    version: "1.x"
    params:
      beta: 0.95
      vision_policy: "circle"
  
  matching:
    name: "three_pass_pairing"
    version: "1.x"
  
  bargaining:
    name: "compensating_block"
    version: "2.x"
    params:
      dA_max: 5
      price_grid: "min_mid_max"

movement_policy:
  name: "deterministic_grid_v1"

foraging_policy:
  name: "single_harvester_v1"
  params:
    enforce: true
```

**Critical:** Default configuration must reproduce current behavior exactly (backward compatibility).

---

## Migration Plan (Safe & Reversible)

### Phase 1: Adapters (No Breaking Changes)
1. Create `src/vmt_engine/protocols/` directory
2. Define `ProtocolBase`, `Effect` types, validator
3. Implement **default adapters** that wrap existing code:
   - `distance_discounted_search`
   - `three_pass_pairing`
   - `compensating_block_bargaining`
   - `deterministic_grid_movement`
   - `single_harvester_foraging`
4. Verify adapters produce identical effects to current implementation
5. Add telemetry: `protocol_runs` table with names/versions

### Phase 2: First Alternative (Proof of Isolation)
1. Implement `random_walk_search` (simple, pedagogical)
2. Create test scenario comparing it to `distance_discounted_search`
3. Verify determinism, telemetry logging, GUI dropdown selection

### Phase 3: First Bargaining Alternative (Economic Validation)
1. Implement `take_it_or_leave_it_bargaining` (single-tick, monopoly power)
2. Create 2-agent money scenario
3. Compare prices/outcomes with `compensating_block_bargaining`
4. **Economic insight:** Quantify surplus distribution differences

### Phase 4: Refactor Core (Remove Old Code)
1. Rewrite `DecisionSystem` to call protocol interfaces
2. Remove inlined logic (now in adapters)
3. Verify all 316+ tests still pass
4. Update documentation

**Timeline Estimate:** 2-3 months at current pace.

---

## Critical Files to Review Next Session

### Current Architecture (Study Before Modifying)
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/src/vmt_engine/simulation.py`
  - **Line ~150-300:** The 7-phase tick loop
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/src/vmt_engine/systems/decision.py`
  - **Monolith to decompose:** Search + matching currently entangled
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/src/vmt_engine/systems/trading.py`
  - **Bargaining logic:** Compensating blocks, price grid, rounding
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/src/vmt_engine/systems/matching.py`
  - **Surplus calculation:** Money-aware pairing (recently fixed P0)

### Related Design Documents
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/docs/proposals/protocol_modularization_plan_v3.md`
  - **Earlier iteration:** May have complementary details
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/docs/2_technical_manual.md`
  - **Current system:** 7-phase description, data flows

### Testing Infrastructure
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/tests/test_pairing_money_aware.py`
  - **Golden tests:** Must pass with adapters
- `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/tests/test_barter_integration.py`
  - **Regression tests:** Bit-identical reproduction requirement

---

## Decision Points for Next Session

### Immediate Question
**Do you want to proceed with the migration plan as outlined?**

Options:
1. **Yes, start Phase 1:** Create protocol directory and adapter stubs
2. **Refine design first:** Review older proposals, check for conflicts
3. **Prototype proof-of-concept:** Build minimal `random_walk_search` outside engine first
4. **Economic validation:** Write formal properties you want each protocol to satisfy

### Secondary Questions
1. **Complexity budgets:** Are the O() bounds specified adequate? (Section 5 of quickreview.md)
2. **Telemetry schema:** Do you need additional columns for experimental design?
3. **GUI integration:** How should protocol selection UI work in launcher?
4. **Documentation:** Level of economic formalism in protocol docstrings?

---

## Context You May Have Forgotten

### Recent History
- **2025-10-22:** P0 Money-Aware Pairing completed
  - Fixed pairing-trading mismatch in money/mixed regimes
  - `estimate_money_aware_surplus()` now used in decision phase
- **Current Status:** All 316+ tests passing
- **Stable Features:** 5 utility functions, SQLite telemetry, PyQt6 launcher

### Strategic Roadmap Position
- **Phase B Complete:** Money system with quasilinear utility
- **Phase C Blocked:** Need protocol modularization first
- **Phase C Goals:** Posted-price markets, auctions, multi-tick bargaining
- **Long-term:** KKT lambda mode (endogenous money demand)

### Key Constraints
- **No SemVer:** Manual version control only
- **Determinism:** Bit-identical reproduction required for all protocols
- **Backward Compatibility:** Default configuration must match current behavior
- **Performance:** Sub-second ticks for N=100 agents (pedagogical scale)

---

## Quick Start Commands (Next Session)

### Review Current Code
```bash
# Read the 7-phase loop
grep -n "def tick" src/vmt_engine/simulation.py

# Read decision system monolith
grep -n "class DecisionSystem" src/vmt_engine/systems/decision.py

# Read trading/bargaining logic
grep -n "compensating block" src/vmt_engine/systems/trading.py
```

### Run Tests (Baseline Before Changes)
```bash
# Full suite (should pass all 316+)
pytest

# Pairing logic (critical for adapters)
pytest tests/test_pairing_money_aware.py -v

# Barter regression (bit-identical check)
pytest tests/test_barter_integration.py -v
```

### Review Documentation
```bash
# Open technical manual
open docs/2_technical_manual.md

# Compare protocol proposals
diff docs/proposals/protocol_modularization_plan_v3.md docs/proposals/quickreview.md
```

---

## Key Insights to Carry Forward

### Architectural
1. **Effect system is the key:** Protocols return intents, core applies them
2. **WorldView immutability:** Prevents race conditions, enables determinism
3. **Multi-tick state:** `InternalStateUpdate` effect handles bargaining rounds
4. **RNG streams:** Per-protocol isolation prevents cross-contamination

### Economic
1. **Mechanism design laboratory:** Each protocol is a testable institution
2. **Comparative statics:** Same agents, different protocols → isolate mechanism effects
3. **Robustness:** Theory predictions should hold across implementations
4. **Publication quality:** Telemetry + versioning enables reproducible research

### Software Engineering
1. **Default adapters:** Preserve existing behavior, enable incremental migration
2. **Safe rollback:** Old code stays until adapters proven equivalent
3. **Test-driven:** Each protocol needs property-based tests
4. **Complexity budgets:** Document O() bounds, enforce in CI

---

## If You Only Have 15 Minutes

1. **Re-read:** Sections 1-3 of `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/docs/proposals/quickreview.md`
2. **Skim:** `/Users/cmfunderburk/CODE_PROJECTS/vmt-dev/src/vmt_engine/systems/decision.py` (the monolith)
3. **Decide:** Do you want to start Phase 1 (adapters) or refine design further?

## If You Have 1-2 Hours

1. **Deep read:** All of `quickreview.md` with `2_technical_manual.md` side-by-side
2. **Code review:** Trace one tick through `simulation.py` → `decision.py` → `trading.py`
3. **Sketch:** Draft `ProtocolBase` ABC and `Effect` types in a scratch file
4. **Plan:** Write concrete task list for Phase 1 adapter implementation

---

## Final Note

You are transitioning from **implementation mode** (P0 money-aware pairing) to **architectural design mode** (protocol modularization). This is a good stopping point because:

1. **Clean slate:** P0 complete, all tests passing
2. **Clear target:** quickreview.md provides detailed specification
3. **Reversible:** Migration plan allows safe rollback
4. **High leverage:** This unblocks all Phase C features

The next session should start with a **decision:** implement as specified, or refine design further. Both are valid choices depending on your confidence level and time constraints.

**Recommended first action next session:** Create a `TODO.md` in `docs/tmp/` with atomic tasks for Phase 1, then decide whether to proceed or iterate on design.

---

**Document Status:** Ready for next session (2025-10-25)  
**Author:** AI assistant (Claude Sonnet 4.5)  
**Purpose:** Re-entry orientation for protocol modularization initiative

