# VMT Project Status Review

**Date:** 2025-11-08
**Status:** Current state as of latest commits

---

## Executive Summary

VMT (Visualizing Microeconomic Theory) is a spatial agent-based simulation platform for studying microeconomic exchange mechanisms. The project has completed foundational work (Stages 0-2) and is positioned to begin Stage 3 (Game Theory Track). Recent work focused on protocol architecture refactoring, type system improvements (int→Decimal), and code cleanup.

**Current State:** Stable barter-only economy with modular protocol system  
**Next Major Milestone:** Stage 3 - Game Theory Track (Edgeworth Box visualization, bargaining solutions)  
**Architecture:** Three-track vision (Agent-Based, Game Theory, Neoclassical) with shared core primitives

---

## Recent Work (Last 2-3 Weeks)

### Major Refactoring: Protocol Architecture Decoupling (2025-11-03 to 2025-11-04)

**Matching-Bargaining Decoupling:**
- Separated matching protocols from bargaining implementations
- `BargainingProtocol.negotiate()` now receives agents directly (breaking change)
- `ProtocolContext` includes agents dict for matching protocols
- Eliminated all "params hacks" (both bargaining and matching)
- Renamed `legacy_compensating_block` → `compensating_block`

**Bargaining Protocol Correction:**
- Removed incorrect `TradeDiscoverer` abstraction
- Inlined search logic into `CompensatingBlockBargaining`
- Converted `SplitDifference` and `TakeItOrLeaveIt` to honest stubs (not_implemented)
- Added `trade_tuple_to_effect()` shared utility
- Clarified principle: protocols define complete mechanisms, not just allocation rules

**Benefits:**
- Independent protocol development
- Cleaner architecture with correct semantic separation
- Matching uses lightweight heuristics; bargaining uses full discovery

### Type System: Int to Decimal Conversion

**Rationale:** Fixed-precision decimal arithmetic for economic quantities
- All goods quantities now use `Decimal` (4 decimal places)
- Prevents floating-point precision errors
- Database storage uses integer minor units (multiplies by 10^4)

**Impact:** Core data structures updated; backward compatibility maintained via conversion utilities

### Code Cleanup & Documentation

**Removed:**
- Legacy code and docstring cleanup passes
- Archive folder (moved to `docs/planning/reference/`)
- Quickfixes documentation (deleted from repo)
- Outdated references in README/tech manual

**Organized:**
- Planning directory restructured
- Reference materials consolidated

---

## Current Architecture

### Project Structure

```
vmt-dev/
├── src/
│   ├── vmt_engine/         # Core simulation engine
│   │   ├── agent_based/    # Search protocols (spatial, agent perspective)
│   │   ├── game_theory/    # Matching & bargaining protocols (global perspective)
│   │   ├── systems/        # Phase-specific execution logic
│   │   ├── core/           # Agents, Grid, Inventory, state management
│   │   └── econ/           # Utility functions (CES, Linear, Quadratic, etc.)
│   ├── vmt_launcher/       # PyQt6 GUI launcher
│   └── vmt_log_viewer/     # Interactive telemetry database viewer
├── scenarios/              # YAML configuration files
├── docs/                   # Documentation and planning
├── tests/                  # Pytest suite (determinism critical)
└── scripts/                # Analysis and utility scripts
```

### The 7-Phase Tick Cycle

Each simulation tick executes 7 phases in strict deterministic order:

1. **Perception**: Agents observe local environment (frozen snapshot)
2. **Decision**: 
   - Search protocol selects targets (builds preference lists)
   - Matching protocol forms trading pairs (3-pass algorithm: mutual consent + greedy fallback)
   - Resource claiming (prevents clustering)
3. **Movement**: Agents move toward targets (deterministic tie-breaking)
4. **Trade**: Paired agents negotiate via bargaining protocol
   - Only `compensating_block` is fully implemented
   - `split_difference` and `take_it_or_leave_it` are stubs
5. **Forage**: Unpaired agents harvest resources
6. **Resource Regeneration**: Resources regrow over time
7. **Housekeeping**: Quote refresh, pairing integrity, telemetry logging

### Protocol System

**Three Protocol Categories:**

1. **Search Protocols** (`agent_based.search`)
   - Agent perspective, uses `WorldView`
   - Examples: `distance_discounted`, `myopic`, `random_walk`
   - Build preference lists from local observations

2. **Matching Protocols** (`game_theory.matching`)
   - Global perspective, uses `ProtocolContext`
   - Examples: `three_pass_matching`, `greedy_surplus`, `random_matching`
   - Forms committed trading pairs

3. **Bargaining Protocols** (`game_theory.bargaining`)
   - Receives agents directly (post-decoupling)
   - Examples: `compensating_block` (implemented), `split_difference` (stub), `take_it_or_leave_it` (stub)
   - Self-contained search + allocation logic

**Protocol Registry:**
- Auto-registration via decorator
- YAML configuration support
- CLI arguments override YAML

### Economic Model

**Current State: Pure Barter Economy**
- Direct A↔B exchanges only
- No money system (removed or not yet implemented)
- Utility functions: CES, Linear, Quadratic, Stone-Geary, Translog
- Reservation pricing via MRS (Marginal Rate of Substitution)
- Quote-based trade evaluation (heuristic for matching, full utility for bargaining)

**Trade Discovery:**
- `compensating_block`: Discrete quantity search (1, 2, 3, ...) with price candidates
- Searches both directions (i gives A, j gives A)
- Returns first mutually beneficial trade (both ΔU > ε)
- Full utility calculations (not heuristics)

### Data Types & Precision

**Core Primitives:**
- `Quantity`: `Decimal` (4 decimal places, quantized)
- `Price`: `float` (exchange rate)
- `UtilityVal`: `float`
- `AgentID`: `int` (non-negative, unique)
- `Tick`: `int` (simulation time step)

**Storage:**
- Database uses integer minor units (multiplies by 10^4)
- Conversion utilities: `to_storage_int()`, `from_storage_int()`

### Telemetry System

**SQLite Database** (`logs/telemetry.db`):
- Agent snapshots (inventory, position, quotes)
- Trades (buyer, seller, quantities, prices)
- Decisions (targets, preferences)
- Resources (positions, amounts)
- Pairings (pair/unpair events)
- Tick states (mode, regime per tick)

**Log Viewer:**
- Interactive PyQt6 GUI
- Timeline scrubber
- Agent state analysis
- Trade history
- CSV export

---

## Implementation Status

### ✅ Completed (Stages 0-2)

**Stage 0: Protocol Restructure**
- Moved protocols to domain-specific modules
- Search → `agent_based.search`
- Matching/Bargaining → `game_theory.matching` / `game_theory.bargaining`
- **Registry System**: The `ProtocolRegistry` is the **active mechanism** for protocol discovery and instantiation, not just legacy compatibility. It serves multiple critical functions:
  - **YAML Configuration**: Protocols are specified by name in scenario YAML files (e.g., `search_protocol: "distance_discounted"`). The registry maps these string names to protocol classes, enabling declarative protocol selection without hardcoded imports.
  - **Runtime Instantiation**: The `protocol_factory.py` functions (`get_search_protocol()`, `get_matching_protocol()`, `get_bargaining_protocol()`) use the registry to instantiate protocols from configuration. This happens at simulation startup when loading scenarios.
  - **Validation**: The scenario schema validator (`schema.py`) queries the registry to verify that protocol names in YAML are valid, providing clear error messages with available alternatives if invalid.
  - **Auto-Registration**: Protocols register themselves via the `@register_protocol` decorator when their modules are imported. This eliminates manual registration and ensures all protocols are discoverable.
  - **Metadata Discovery**: The registry stores and provides protocol metadata (version, description, complexity, properties, references) for documentation, UI display, and protocol catalogs.
  - **Decoupling**: The registry enables the simulation engine to instantiate protocols by name without knowing their module locations, allowing protocols to be reorganized (as in Stage 0) without breaking scenario files or simulation code.
  
  **Post-Refactor Status**: The registry remains essential because it provides the abstraction layer between protocol names (as specified in YAML) and protocol implementations (now in domain-specific modules). Without it, scenario files would need to specify full import paths, and protocol reorganization would break existing scenarios.

**Stage 1: Foundational Analysis**
- Core simulation engine
- Agent-based model with spatial grid
- Utility functions (CES, Linear, Quadratic, Stone-Geary, Translog)
- Barter trading system
- Deterministic execution

**Stage 2: Protocol Diversification**
- Multiple search protocols
- Multiple matching protocols
- Trade pairing system (3-pass algorithm)
- Resource claiming system
- Visualization enhancements (target arrows, smart co-location)

**Infrastructure:**
- SQLite telemetry system
- PyQt6 launcher and log viewer
- Comprehensive test suite
- Documentation system

### 🔵 Next Up: Stage 3 - Game Theory Track

**Purpose:** Build interactive Edgeworth Box visualization and implement bargaining solutions

**Planned Components:**
1. **Two-Agent Exchange Engine**
   - Contract curve computation (Pareto efficient allocations)
   - Competitive equilibrium solver
   - Agent optimization methods

2. **Interactive Edgeworth Box Visualization**
   - Matplotlib-based visualization
   - Slider controls for allocation
   - Indifference curve display
   - Contract curve overlay
   - Competitive equilibrium display

3. **Bargaining Solutions**
   - Nash bargaining solution
   - Kalai-Smorodinsky solution
   - Rubinstein alternating offers

4. **Protocol Testing Framework**
   - Test protocols in Game Theory context
   - Compare outcomes
   - Validate theoretical predictions

**Duration:** Weeks 7-12 (per roadmap)  
**Status:** Not yet started

### ⚪ Planned (Stages 4-6)

**Stage 4: Unified Launcher**
- Single interface for all three tracks
- Scenario selection across tracks
- Track-specific configuration

**Stage 5: Market Information Systems**
- Emergent price discovery
- Spatial market area detection
- Information broadcasting
- Agent memory systems

**Stage 6: Neoclassical Benchmarks**
- Walrasian auctioneer
- Tatonnement process
- General equilibrium solver
- Stability analysis

---

## Key Design Principles

### 1. Determinism
- All simulations are fully deterministic
- Same scenario + seed = identical outcomes
- Critical for research validity
- Uses `sim.rng` (never `random` module)

### 2. Protocol Ownership
- `game_theory/` owns: Bargaining and Matching protocols
- `agent_based/` owns: Search protocols (inherently spatial)
- Agent-Based track imports Game Theory protocols for consistency

### 3. Three-Track Paradigm
- **Agent-Based Track**: Emergent market phenomena from spatial bilateral trading
- **Game Theory Track**: Strategic interactions with Edgeworth Box visualizations
- **Neoclassical Track**: Equilibrium benchmarks using traditional solution methods
- All tracks share economic primitives (Agent, Utility, Trade)

### 4. Protocol Self-Containment
- Protocols define complete mechanisms (search + allocation)
- No external abstractions (e.g., `TradeDiscoverer` removed)
- Matching uses lightweight heuristics; bargaining uses full discovery

### 5. Type Safety
- `Decimal` for all economic quantities (no floats)
- Fixed precision (4 decimal places)
- Database storage via integer minor units

---

## Testing Status

**Test Framework:** `pytest`

**Key Test Categories:**
- Determinism tests (critical: same seed = identical outcomes)
- Protocol tests (search, matching, bargaining)
- Utility function tests (all types)
- Integration tests (full simulation runs)
- Trade evaluation tests
- Resource claiming tests
- Pairing system tests

**Test Location:** `tests/` directory

**Note:** Test count and status should be verified by running `pytest` (requires venv activation)

---

## Documentation Status

### Current Documentation

**Core Docs:**
- `README.md`: Project overview and quick start
- `docs/1_technical_manual.md`: Detailed technical overview
- `docs/2_typing_overview.md`: Type system and data contracts
- `docs/3_enhancement_backlog.md`: Quality-of-life improvements (marked as outdated)

**Planning Docs:**
- `docs/planning/0_VMT_Roadmap.md`: Master roadmap
- `docs/planning/1_Implementation_Stage3_GameTheory.md`: Stage 3 detailed plan
- `docs/planning/2_Implementation_Stage4_Launcher.md`: Stage 4 plan
- `docs/planning/3_Implementation_Stage5_MarketInfo.md`: Stage 5 plan
- `docs/planning/4_Implementation_Stage6_Neoclassical.md`: Stage 6 plan

**Reference:**
- `docs/planning/reference/`: Foundational theoretical documents

### Documentation Gaps

- `docs/3_enhancement_backlog.md` marked as "OUTDATED -- NEEDS A THOROUGH REWRITE"
- Some references to money system in docs (may be outdated)
- Scenario template mentions money system removal (verify current state)

---

## Known Issues & Technical Debt

### Protocol Implementation Gaps

**Bargaining Protocols:**
- `split_difference`: Stub only (not_implemented)
- `take_it_or_leave_it`: Stub only (not_implemented)
- Only `compensating_block` is fully functional

<!-- ### Money System Status

**Current State: REMOVED**
- CHANGELOG shows money system was implemented (pre-release 2025-10-21)
- Scenario template explicitly states: "MONEY SYSTEM REMOVED: VMT is now a pure barter economy"
- No money-related code found in current codebase (grep search returned no matches)
- **Conclusion:** Money system was implemented then removed; current state is pure barter economy
- **Action Required:** Update CHANGELOG to reflect removal, or move money system entries to archived section

### Documentation Inconsistencies

- Enhancement backlog marked as outdated
- Money system references may be stale
- Some planning docs may reference removed features -->

---

## Next Steps & Recommendations

### Immediate Actions

<!-- 
1. **Verify Money System Status**
   - Check git history for money system removal
   - Update documentation to reflect current state
   - Remove or update stale references -->

2. **Run Test Suite**
   - Activate venv: `source venv/bin/activate`
   - Run: `pytest`
   - Verify all tests pass
   - Document test count and any failures

3. **Review Recent Changes**
   - Review protocol decoupling changes
   - Understand new architecture
   - Test with existing scenarios

### Short-Term (Before Stage 3)

<!-- 1. **Documentation Cleanup**
   - Update enhancement backlog or remove if obsolete
   - Update CHANGELOG to clarify money system removal
   - Remove or archive outdated money system references -->

2. **Code Review**
   - Review protocol decoupling implementation
   - Verify backward compatibility
   - Check for any breaking changes in scenarios

3. **Test Coverage**
   - Ensure new protocol architecture is well-tested
   - Add tests for edge cases
   - Verify determinism still holds

### Medium-Term (Stage 3 Preparation)

1. **Study Stage 3 Plan**
   - Review `docs/planning/1_Implementation_Stage3_GameTheory.md`
   - Understand Edgeworth Box requirements
   - Plan implementation approach

2. **Dependencies Check** ⚠️ **ACTION REQUIRED**
   - **Missing:** `matplotlib` and `scipy` are required for Stage 3 but not in `requirements.txt`
   - Add `matplotlib>=3.7.0` for Edgeworth Box visualization
   - Add `scipy>=1.10.0` for optimization methods (contract curve, equilibrium solving)
   - Update `requirements.txt` before starting Stage 3

3. **Architecture Alignment**
   - Ensure Game Theory track aligns with three-track vision
   - Plan integration with Agent-Based track
   - Design protocol testing framework

---

## Key Files to Review

### Core Architecture
- `src/vmt_engine/core/agent.py`: Agent state and behavior
- `src/vmt_engine/core/state.py`: Inventory, Quote, core data structures
- `src/vmt_engine/simulation.py`: Main simulation loop (7-phase cycle)
- `src/vmt_engine/systems/`: Phase execution logic

### Protocol System
- `src/vmt_engine/protocols/base.py`: Protocol base classes
- `src/vmt_engine/protocols/registry.py`: Protocol registration
- `src/vmt_engine/game_theory/bargaining/compensating_block.py`: Main bargaining protocol
- `src/vmt_engine/game_theory/matching/three_pass.py`: Main matching protocol
- `src/vmt_engine/agent_based/search/distance_discounted.py`: Main search protocol

### Configuration
- `src/scenarios/schema.py`: Scenario YAML schema
- `src/scenarios/loader.py`: Scenario loading logic

### Testing
- `tests/test_simulation_init.py`: Determinism tests
- `tests/test_*.py`: Various protocol and integration tests

### Documentation
- `docs/planning/0_VMT_Roadmap.md`: Master roadmap
- `docs/planning/1_Implementation_Stage3_GameTheory.md`: Next stage plan
- `CHANGELOG.md`: Recent changes

---

## Questions to Resolve

1. ~~**Money System:** What is the current status?~~ ✅ **RESOLVED:** Removed (confirmed via codebase search and scenario template)
2. **Test Status:** How many tests pass? Any known failures? (Run `pytest` to verify)
3. **Breaking Changes:** Are there any breaking changes from recent refactoring that affect existing scenarios?
4. **Stage 3 Timeline:** Is the "Weeks 7-12" timeline still accurate? What is the actual start date?
5. ~~**Dependencies:** Are all required libraries for Stage 3 (matplotlib, scipy) in requirements.txt?~~ ⚠️ **RESOLVED:** Missing - need to add matplotlib and scipy before Stage 3

---

## Conclusion

VMT is in a stable state with a solid foundation (Stages 0-2 complete). Recent protocol architecture refactoring has improved code organization and separation of concerns. The project is well-positioned to begin Stage 3 (Game Theory Track), which will add interactive Edgeworth Box visualization and bargaining solution implementations.

**Key Strengths:**
- Clean protocol architecture (post-decoupling)
- Comprehensive telemetry system
- Strong documentation and planning
- Deterministic execution
- Modular, extensible design

**Areas for Attention:**
- Clarify money system status
- Update outdated documentation
- Verify test suite status
- Prepare for Stage 3 implementation

**Recommended Next Action:** Verify test suite, clarify money system status, then begin Stage 3 planning and implementation.

---

**Document Version:** 0.1.0
**Last Updated:** 2025-11-06
**Next Review:** After Stage 3 completion or major architectural changes

