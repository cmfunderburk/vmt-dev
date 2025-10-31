# VMT (Visualizing Microeconomic Theory) - AI Agent Instructions

## Project Mission & Philosophy

VMT is a **spatial agent-based simulation** for studying how market phenomena **emerge** from micro-level interactions. Unlike traditional economics that assumes equilibrium prices or centralized coordination, VMT demonstrates when/how markets form through **explicit agent behaviors and institutional mechanisms**: search protocols, matching algorithms, and bargaining rules.

**Core Principle**: No external calculus. Markets, prices, and money must emerge from agent interactions—never imposed from above.

## Current Phase: Scenario Curation & Behavioral Validation (Phase 2.5)

**Priority**: Before implementing new protocols or information mechanisms, validate existing bilateral exchange behavior through carefully designed scenarios.

**Activities**:
- Design scenarios that isolate specific behavioral patterns
- Document actual vs expected protocol outcomes
- Build empirical understanding of search, matching, and bargaining interactions
- Create pedagogical examples demonstrating core mechanisms

**Why First**: Can't build extensions on unstable foundation. Must understand current behavior deeply before adding complexity.

## Critical Architecture: Protocol → Effect → State

**This is THE fundamental pattern. NO EXCEPTIONS.**

### The Flow (7-Phase Tick Cycle)
```
1. Perception    → Agents observe frozen WorldView snapshot
2. Decision      → Protocols generate Effects (search + matching)
3. Movement      → MoveEffect changes agent positions  
4. Trade         → Paired agents negotiate (bargaining protocol returns TradeEffect)
5. Foraging      → HarvestEffect claims resources
6. Regeneration  → Resources regrow
7. Housekeeping  → Quote refresh, telemetry, cleanup
```

### Protocol Pattern
```python
# CORRECT: Protocol returns declarative Effects
class MySearchProtocol(SearchProtocol):
    def execute(self, context: ProtocolContext) -> list[Effect]:
        return [SetTargetEffect(agent_id=1, target_id=2)]

# WRONG: Never mutate state directly
# agent.target = other_agent  # ❌ FORBIDDEN
# agent.position = (5,5)      # ❌ FORBIDDEN
```

**Key files**: 
- `src/vmt_engine/protocols/base.py` - All Effect types
- `src/vmt_engine/systems/` - Phase execution logic
- `src/vmt_engine/core/agent.py` - Agent state (read-only in protocols)

## Determinism is Non-Negotiable

Same seed → **bit-identical results**. Required for scientific validity.

### Mandatory Rules
1. **RNG**: Use ONLY `self.rng` (agents) or `world.rng` (engine). Never `random.random()`, `numpy.random`, time-based sources
2. **Iteration Order**: ALWAYS sort before iterating: `for agent in sorted(agents, key=lambda a: a.id)`
3. **No Unordered Collections**: Never iterate dicts/sets without sorting keys first
4. **Effects Execute in Order**: All state changes via Effect objects applied deterministically

### Test Pattern - ALWAYS Use Virtual Environment
```bash
# CORRECT - All Python commands
bash -c "source venv/bin/activate && python -m pytest tests/test_*.py -v"

# WRONG - Never run outside venv or without bash -c
# python -m pytest  # ❌ Shell may not be bash, venv may not activate
```

**Why**: Non-bash shells may not properly activate venv with `source`. `bash -c` ensures correct execution.

## Pure Barter Economy (Money System Removed - Oct 2025)

**Current State**: VMT is a **pure barter economy**. All trades are direct A↔B good-for-good exchanges.

**What Was Removed**:
- `Inventory.M` field (money)
- `Agent.lambda_money`, `money_utility_form` parameters
- Money-aware utility functions (`u_total()`, `mu_money()`)
- Money quotes (A↔M, B↔M)
- Exchange regimes (`money_only`, `mixed`)

**What Remains**:
- Two goods: A and B
- Utility functions over goods only: `u(A, B)` → float
- Barter quotes: `ask_A_in_B`, `bid_A_in_B`, etc.
- Bilateral negotiation for A↔B exchanges

**Future**: Money will be **re-introduced as emergent phenomenon** (Phase 4), not imposed through utility functions.

## Research Agenda (Updated Oct 2025)

### Phase 1: Baseline Protocols ✅ COMPLETE
- ✅ Legacy protocols: Distance-discounted search, three-pass matching, compensating block bargaining
- ✅ Effect-based architecture working
- ✅ Pure barter trading (A↔B only)

### Phase 2a: Alternative Bilateral Protocols 🔜 PLANNED
- Simple baselines: Random walk search, random matching, split-the-difference bargaining
- Goal: Comparison of bilateral mechanisms, establish efficiency/fairness baselines

### Phase 2.5: Scenario Curation ⭐ **CURRENT PRIORITY**
- Manually design scenarios that validate/demonstrate protocol behavior
- Build empirical understanding before extending architecture
- Create pedagogical examples
- Document actual behavioral patterns

### Phase 3: Market Information and Coordination 🎯 NEXT
**Philosophy**: Markets are **information aggregators** that enhance bilateral trading, not replacements for it.

**NOT implementing**: Walrasian auctioneer, imposed clearing prices, external equilibrium calculation

**INSTEAD implementing**:
- Information hubs: Agents observe aggregate price signals from recent trades
- Market-informed bargaining: Use market data to inform bilateral negotiations
- Price broadcasting: Disseminate transaction history without imposing coordination
- Convergence study: When do informed bilateral negotiations produce uniform prices?

**Goal**: Study how information affects decentralized price discovery through actual bilateral trading.

### Phase 4: Commodity Money Emergence 🔮 FUTURE
**Philosophy**: Money should **emerge endogenously** from trading patterns, not be valued directly in utility functions.

**Mechanisms**:
- Indirect exchange: Enable multi-step trades (A→B→C paths)
- Marketability differences: Some goods easier to trade than others
- Observation: Agents discover which goods function as better intermediaries
- Salability premium: Goods with higher resale potential become money-like

**Goal**: Demonstrate how money emerges from the "double coincidence of wants" problem.

### Phase 5: Advanced Mechanisms 📚 LONG-TERM
- Memory-based search (learning)
- Stable matching (Gale-Shapley)
- Nash bargaining
- Rubinstein alternating offers
- Network formation

## Protocol System

### Protocol Registry
Protocols auto-discovered via `src/vmt_engine/protocols/registry.py`:
- Scans `protocols/{search,matching,bargaining}/` subdirectories
- YAML scenarios specify by name: `search_protocol: "myopic"`
- Test helper: `make_sim(scenario, search="random_walk", matching="greedy_surplus")`

### Implementing New Protocols
1. Extend base class: `SearchProtocol`, `MatchingProtocol`, or `BargainingProtocol`
2. Implement `execute(context: ProtocolContext) -> list[Effect]`
3. Place in appropriate subdirectory (auto-registered)
4. **Add docstring explaining economic mechanism** (not just code)
5. Write tests using `tests/helpers/builders.py`

**Example files**:
- `src/vmt_engine/protocols/search/myopic.py` - Greedy best-partner search
- `src/vmt_engine/protocols/matching/greedy.py` - Highest surplus matching
- `src/vmt_engine/protocols/bargaining/split_difference.py` - Equal surplus division

## Scenario Files (YAML Configuration)

Located in `scenarios/` (root) and `scenarios/demos/` (curated examples).

### Minimal Barter Scenario
```yaml
schema_version: 1
name: "Simple Barter"
N: 10                    # Grid size (10×10)
agents: 20               # Number of agents

initial_inventories:
  A: [10, 5, 8, ...]     # Per-agent inventories (goods only)
  B: [5, 10, 6, ...]

utilities:
  mix:
    - type: ces          # CES, linear, quadratic, translog, stone_geary
      weight: 0.6
      params: {rho: -0.5, wA: 1.0, wB: 1.0}
    - type: linear
      weight: 0.4
      params: {vA: 1.0, vB: 1.2}

params:
  vision_radius: 10
  interaction_radius: 1
  dA_max: 5              # Max trade size to search
  spread: 0.0            # Quote spread (0 = no spread)
  
# Optional protocol overrides
search_protocol: "myopic"
matching_protocol: "greedy_surplus"
bargaining_protocol: "split_difference"
```

**Schema**: `src/scenarios/schema.py` for all available parameters.

## Running Simulations

### GUI (Recommended for Exploration)
```bash
python launcher.py
```

### CLI (Reproducible Runs)
```bash
python main.py scenarios/demos/minimal_2agent.yaml 42  # seed=42
```

### Headless (Analysis/Testing)
```python
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation

scenario = load_scenario("scenarios/demos/minimal_2agent.yaml")
sim = Simulation(scenario, seed=42)
sim.run(max_ticks=100)
```

## Test Suite (300+ Tests)

### Test Structure
- `tests/test_*.py` - Individual test files
- `tests/helpers/` - Shared utilities
  - `builders.py` - `build_scenario()`, `make_sim()` helpers
  - `run.py` - `run_ticks()` execution helpers
  - `assertions.py` - Domain-specific assertions

### Test Pattern
```python
from tests.helpers import builders, run_helpers

def test_protocol_behavior():
    scenario = builders.build_scenario(N=10, agents=4)
    sim = builders.make_sim(scenario, seed=42, matching="greedy_surplus")
    run_helpers.run_ticks(sim, 10)
    
    # Verify behavior
    assert sim.tick == 10
    assert len([a for a in sim.agents if a.target_id is not None]) >= 0
```

### Running Tests
```bash
# Single test file
bash -c "source venv/bin/activate && python -m pytest tests/test_greedy_surplus_matching.py -v"

# All tests
bash -c "source venv/bin/activate && python -m pytest tests/ -v"

# With coverage
bash -c "source venv/bin/activate && python -m pytest tests/ --cov=src/vmt_engine --cov-report=html"
```

## Documentation Structure

**Essential Reading**:
- `README.md` - Quick start, overview
- `docs/BIGGEST_PICTURE/vision_and_architecture.md` - Strategic vision, research agenda (READ Phase 2.5-4 sections!)
- `docs/2_technical_manual.md` - 7-phase cycle, economic logic, current protocols
- `.cursor/rules/*.mdc` - Architecture rules (determinism, test execution, planning discipline)

**Current Development**:
- `docs/CURRENT/` - Active development notes, protocol status
- `docs/market_brainstorms/` - Phase 3 design thinking (information hubs, price signals)
- `docs/CURRENT/critical/` - Deep architectural analyses

**Reference**:
- `docs/1_project_overview.md` - Feature documentation
- `docs/structures/` - Scenario templates and parameter reference

## Common Workflows

### Adding a New Bilateral Protocol (Phase 2a/2b)
1. Create file: `src/vmt_engine/protocols/{search|matching|bargaining}/my_protocol.py`
2. Extend base class, implement `execute()` returning `list[Effect]`
3. Add docstring explaining **economic mechanism** (e.g., "Maximizes total surplus" or "Ensures stability")
4. Write tests in `tests/test_my_protocol.py` using `builders` helpers
5. Run: `bash -c "source venv/bin/activate && python -m pytest tests/test_my_protocol.py -v"`
6. Update protocol registry documentation if needed

**Safe for implementation**: Well-understood, extends existing interfaces.

### Creating a Curated Scenario (Phase 2.5) ⭐ **CURRENT FOCUS**
1. Copy template from `scenarios/demos/` or use `docs/structures/minimal_working_example.yaml`
2. Add pedagogical comment header explaining learning objective
3. Design **complementary inventories** to create trading opportunities (e.g., agent 0 has excess A, wants B; agent 1 opposite)
4. Choose utility functions that produce clear incentives
5. Test: `python main.py scenarios/my_scenario.yaml 42`
6. Document expected behavior vs actual behavior
7. Iterate until scenario reliably demonstrates intended pattern

**Purpose**: Build empirical foundation, understand protocol behavior, create teaching materials.

### Debugging Determinism Issues
1. Check all RNG calls use `self.rng` / `world.rng` (grep for `random.` or `np.random`)
2. Verify iteration order: `sorted(agents, key=lambda a: a.id)` before any loops
3. Confirm Effects used for all state changes (no direct mutations)
4. Run twice with same seed, compare outputs
5. Check telemetry databases for divergence point

### Planning Phase 3 Work (Market Information) 🚧
**CRITICAL**: Phase 3 requires architectural design discussion BEFORE implementation.

**Questions to answer first**:
- How do agents observe aggregate price information? New fields in `WorldView`?
- Where in 7-phase cycle does information aggregation occur? New system?
- How does information affect bilateral bargaining? New `ProtocolContext` data?
- What's the pedagogical story: "Information enhances coordination" not "Markets impose equilibrium"

**Pattern**: Design → Discuss → Document → Implement (in that order).

## Code Style Conventions

- **Type hints**: Required for public APIs, protocols, Effect classes
- **Docstrings**: All protocols must explain economic mechanism, not just interface
- **Immutability**: `WorldView`/`ProtocolContext` are read-only snapshots
- **Naming**: `dA_max` (trade size), `N` (grid size), `beta` (discount factor)
- **Tests**: Use `builders` helpers, never raw `Simulation` construction
- **Comments**: Explain "why" (economic intuition), not "what" (code is self-documenting)

## Critical Rules: Planning Before Implementation

**When working on complex features (Phase 3+, architectural changes)**:
1. ✅ **DO**: Discuss design, clarify requirements, document approach
2. ✅ **DO**: Ask questions about integration with 7-phase cycle
3. ✅ **DO**: Explain tradeoffs and alternatives
4. ❌ **DON'T**: Make code changes until user says "start implementing"
5. ❌ **DON'T**: Assume you know the "right" solution without discussion

**Rationale**: Complex features often have hidden architectural implications. Better to discover issues during design than after implementation.

## Open Research Questions (Guide Discussion, Don't "Solve")

### Phase 3: Information Mechanisms
- How should price information be represented? Time-weighted average? Last N trades? Spatial distribution?
- Should information be global (all agents see same data) or local (distance-based)?
- How does information affect bargaining? Better BATNAs? Tighter spreads? Focal points?
- Can we avoid creating "magic" information channels that break spatial realism?

### Phase 4: Money Emergence
- How to model "indirect exchange" in a tick-based system? Multi-tick trading chains?
- What makes a good "salable"? Objective metric or subjective perception?
- Should agents "learn" which goods are money-like? How to represent that knowledge?
- How does double coincidence of wants actually create trading frictions in the simulation?

**For AI Agents**: When user asks about these topics, lead with questions, explore alternatives, discuss tradeoffs. Design before coding.

---

**Quick Reference Files**:
- Architecture: `src/vmt_engine/protocols/base.py` (Effects), `src/vmt_engine/systems/` (phases)
- Core Types: `src/vmt_engine/core/agent.py`, `src/vmt_engine/core/grid.py`
- Scenarios: `src/scenarios/schema.py`, `scenarios/demos/*.yaml`
- Testing: `tests/helpers/builders.py`, `pytest.ini`
- Vision: `docs/BIGGEST_PICTURE/vision_and_architecture.md` (Phases 2.5-4)
- Rules: `.cursor/rules/*.mdc` (architecture, test execution, determinism)

