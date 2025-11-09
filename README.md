# VMT – Visualizing Microeconomic Theory

A modular agent-based simulation platform for studying microeconomic exchange mechanisms through interactive comparison of institutional designs. VMT lets you build markets from individual agent interactions, compare emergent outcomes with economic theory, and understand why institutional details matter.

## The Core Insight

Markets are **institutional constructions**, not natural phenomena. VMT demonstrates how market-like behavior—or the lack thereof—emerges from:
- **Agent interactions** (bilateral bargaining, resource competition)
- **Institutional rules** (search protocols, matching mechanisms, bargaining procedures)
- **Spatial environments** (search costs, information asymmetries, clustering)

Instead of assuming equilibrium, VMT models the *process* of exchange.

---

## Three-Track Vision

VMT is architected as a comprehensive pedagogical and research platform with three complementary paradigms:

### 1. **Agent-Based Track** 🗺️
Emergent market phenomena from spatial bilateral trading. Agents with heterogeneous preferences operate in a spatial environment, foraging for resources and trading with one another based on configurable institutional rules.

**Use cases:**
- Study how geography influences economic activity
- Compare different search and matching protocols
- Observe market failures and inefficiencies
- Understand path-dependency and coordination problems

### 2. **Game Theory Track** 📈
Strategic interactions with rigorous theoretical grounding. Two-agent Edgeworth Box visualizations, contract curve computation, and implementation of classic bargaining solutions (Nash, Kalai-Smorodinsky, etc.).

**Use cases:**
- Interactive Edgeworth Box exploration
- Comparative analysis of bargaining protocols
- Validate experimental outcomes against theory
- Teach core microeconomic concepts

### 3. **Neoclassical Track** ⚖️  
Equilibrium benchmarks using traditional solution methods (Walrasian auctioneer, tatonnement, general equilibrium solvers).

**Use cases:**
- Compute theoretical benchmarks for comparison
- Study stability of equilibria
- Analyze welfare implications of different mechanisms
- Research general equilibrium properties

---

## Quick Start

### Installation

```bash
# Clone repository
git clone [repository-url] vmt-dev
cd vmt-dev

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run a Simulation

**GUI (Recommended for exploration):**
```bash
python launcher.py
```
Select a scenario from `scenarios/demos/` to run and visualize in real-time.

**Command Line:**
```bash
python main.py scenarios/demos/minimal_2agent.yaml
```

**View Results:**
```bash
python view_logs.py  # Open interactive telemetry viewer
```
The telemetry database (`logs/telemetry.db`) contains detailed tick-by-tick logs of agent state, trades, and decisions—the primary debugging tool.

---

## How It Works: The 7-Phase Tick Cycle

Each simulation tick follows a deterministic cycle:

1. **Perception** — Agents observe local environment (frozen snapshot)
2. **Decision** — Multi-step orchestration:
   - Search protocol identifies potential partners/targets
   - Matching protocol forms committed trading pairs
   - Resource claims made (prevents clustering)
3. **Movement** — Agents move toward targets (deterministic tie-breaking)
4. **Trade** — Paired agents negotiate via bargaining protocol
5. **Forage** — Unpaired agents harvest resources
6. **Resource Regeneration** — Resources regrow per scenario rules
7. **Housekeeping** — Quote updates, pairing integrity, telemetry logging

**Key Property:** Full determinism. Same scenario + seed = identical outcomes. Critical for research validity.

---

## Project Structure

```
vmt-dev/
├── src/
│   ├── vmt_engine/           # Core simulation engine
│   │   ├── agent_based/      # Search protocols (spatial perspective)
│   │   ├── game_theory/      # Matching & bargaining protocols (strategic perspective)
│   │   ├── systems/          # Phase-specific execution logic
│   │   ├── core/             # Agents, grid, inventory, state primitives
│   │   └── econ/             # Utility functions (CES, Linear, Quadratic, Stone-Geary, Translog)
│   ├── vmt_launcher/         # PyQt6 GUI launcher
│   ├── vmt_log_viewer/       # Interactive telemetry database viewer
│   └── telemetry/            # SQLite logging system
├── scenarios/
│   ├── baseline/             # Standard test scenarios
│   ├── demos/                # Pedagogical examples
│   ├── curated/              # Large-scale scenarios
│   └── test/                 # Utility function tests
├── docs/
│   ├── planning/             # Roadmap, stage plans, technical specs
│   ├── CURRENT/              # Active refactoring documentation
│   ├── structures/           # Scenario templates
│   └── *.md                  # Technical manual, typing overview
├── tests/                    # Comprehensive pytest suite (determinism critical!)
└── scripts/                  # Analysis and utility scripts
```

---

## Configuring Scenarios

Simulations are configured via YAML files. Declare protocols and agent properties:

```yaml
# Grid and timing
grid_size: 20
num_agents: 10
max_ticks: 1000

# Institutional rules (protocols)
search_protocol: "distance_discounted"     # How agents find partners
matching_protocol: "greedy_surplus"        # How pairs form
bargaining_protocol: "compensating_block"  # How prices are negotiated

# Agents
agents:
  - utility_function: "ces"
    params: {alpha_A: 0.5, alpha_B: 0.5, rho: 0.5}
    endowment: {A: 10, B: 10}
```

---

## Available Protocols

### Search Protocols (`agent_based.search`)
How agents locate potential partners. *Agent perspective, uses local `WorldView`.*

| Protocol | Description |
|----------|-------------|
| `distance_discounted` | Heuristic: chooses targets within vision radius by discounted utility |
| `myopic` | Greedy search for best nearby opportunity |
| `random_walk` | Random exploration; useful for baseline comparisons |

### Matching Protocols (`game_theory.matching`)
How trading pairs form. *Global perspective, uses `ProtocolContext`.*

| Protocol | Description |
|----------|-------------|
| `three_pass_matching` | 3-pass algorithm: mutual consent, greedy fallback, unpaired pairing |
| `greedy_surplus` | Forms pairs by highest potential gains from trade |
| `random_matching` | Random pairing; baseline comparison |

### Bargaining Protocols (`game_theory.bargaining`)
How prices are negotiated. Self-contained with internal search logic.

| Protocol | Status | Description |
|----------|--------|-------------|
| `compensating_block` | ✅ Implemented | Discrete quantity search with integer-to-decimal block trades. Full utility calculations. |
| `split_difference` | 🔸 Stub | Placeholder for future implementation |
| `take_it_or_leave_it` | 🔸 Stub | Placeholder for future implementation |

**Protocol Registry:** All protocols auto-register via `@register_protocol` decorator. YAML and CLI both support protocol selection by name, enabling declarative mechanism design.

---

## Current State: Pure Barter Economy

VMT currently implements a **direct A↔B barter economy** with no money system. This provides a clean foundation for studying bilateral exchange mechanisms:

- Agents directly exchange goods based on utility
- Reservation prices computed via Marginal Rate of Substitution (MRS)
- Quote-based heuristics for lightweight matching phase
- Full utility calculations for bargaining discovery

**Data Types:**
- **Quantity**: `Decimal` (4 decimal places, fixed precision)
- **Price**: `float` (exchange rate)
- **UtilityVal**: `float`
- **AgentID**: `int`
- **Tick**: `int`

Database storage uses integer minor units (multiplies by 10^4) to avoid floating-point issues.

---

## Development & Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test
pytest tests/test_simulation_init.py -v
```

### Testing Philosophy

**Determinism is critical:**
- Every new feature or protocol must include a determinism test
- Same scenario + seed = identical outcomes
- Use `sim.rng`, never the `random` module
- See `tests/test_simulation_init.py` for examples

**Test Scenarios:**
- Unit tests: use `tests.helpers.scenarios.create_minimal_scenario()`
- Integration tests: use dedicated files in `scenarios/test/`

---

## Documentation

### Quick References
- **[Technical Manual](docs/1_technical_manual.md)** — Deep dive into architecture, data types, and subsystems
- **[Type System Overview](docs/2_typing_overview.md)** — Contracts, data structures, type safety
- **[Project Roadmap](docs/planning/0_VMT_Roadmap.md)** — Long-term vision and implementation stages

### Current Development
- **[Project Status Review](docs/planning/PROJECT_STATUS_REVIEW.md)** — Current state, recent refactoring, known issues
- **[Stage 3 Plan (Game Theory Track)](docs/planning/1_Implementation_Stage3_GameTheory.md)** — Next major phase: Edgeworth Box and bargaining solutions

### Advanced Topics
- **[Stage 4: Unified Launcher](docs/planning/2_Implementation_Stage4_Launcher.md)**
- **[Stage 5: Market Information Systems](docs/planning/3_Implementation_Stage5_MarketInfo.md)**
- **[Stage 6: Neoclassical Benchmarks](docs/planning/4_Implementation_Stage6_Neoclassical.md)**

---

## How to Contribute

### For Newcomers
1. Read **[Technical Manual](docs/1_technical_manual.md)** to understand the architecture
2. Run existing scenarios to see the platform in action
3. Study a protocol implementation (e.g., `compensating_block` bargaining)
4. Start with small extensions (add a new utility function, modify scenario parameters)

### Priority Contribution Areas
1. **Bargaining Protocol Implementation** — Flesh out `split_difference` and `take_it_or_leave_it` protocols
2. **New Search/Matching Mechanisms** — Design and implement new institutional rules
3. **Scenario Development** — Create pedagogical examples that highlight specific phenomena
4. **Analysis Tools** — Build new scripts for visualization and statistical analysis
5. **Documentation** — Improve guides, add examples, clarify edge cases

### Testing Requirements
- All new code must include tests
- All protocol changes must verify determinism
- Use `pytest` to run the suite before submitting

---

## Recent Major Changes

### Protocol Architecture Refactor (Nov 2025)
- **Restructured** protocols into domain-specific modules:
  - Search → `agent_based.search` (spatial, agent perspective)
  - Matching/Bargaining → `game_theory.matching` / `game_theory.bargaining` (strategic perspective)
- **Decoupled** matching from bargaining (independent development, cleaner separation)
- **Simplified** bargaining protocols (self-contained, removed `TradeDiscoverer` abstraction)
- **Clarified** that `split_difference` and `take_it_or_leave_it` are stubs, not implemented
- **Impact**: YAML scenario files unchanged (backward compatible via registry)

### Type System: Integer to Decimal (Nov 2025)
- All economic quantities now use `Decimal` with 4 decimal places
- Prevents floating-point precision errors
- Database storage via integer minor units
- Conversion utilities: `to_storage_int()`, `from_storage_int()`

---

## Known Limitations

| Area | Status | Notes |
|------|--------|-------|
| Bargaining | ⚠️ Partial | Only `compensating_block` fully implemented; `split_difference` and `take_it_or_leave_it` are stubs |
| Money System | ⏸️ Not Implemented | Current economy is pure barter. Theoretically rigorous monetary system planned for future. |
| Learning/Adaptation | ⏸️ Planned | Agent decision-making currently uses static heuristics; learning mechanisms reserved for future expansion |
| Centralized Markets | ⏸️ Planned | Single-protocol implementation only (no Walrasian auctioneer or double auction yet) |

---

## Roadmap

| Stage | Status | Focus |
|-------|--------|-------|
| **0–2** | ✅ Complete | Foundational engine, protocol diversification, telemetry system |
| **3** | 🔵 Next | Game Theory Track: Edgeworth Box visualization, bargaining solutions |
| **4** | ⚪️ Planned | Unified Launcher: single interface for all three tracks |
| **5** | ⚪️ Planned | Market Information: price discovery, information broadcasting |
| **6** | ⚪️ Planned | Neoclassical Track: Walrasian equilibrium, tatonnement, general equilibrium |

See [Project Roadmap](docs/planning/0_VMT_Roadmap.md) for detailed timelines and scope.

---

## The Research Vision

VMT is designed to answer questions like:

- **Institutional Design**: How do search, matching, and bargaining protocols influence outcomes?
- **Spatial Economics**: What is the role of geography and search costs?
- **Emergence**: How do markets arise from individual interactions? When do they fail?
- **Pedagogy**: Can students build better intuition by designing and comparing mechanisms?

It bridges the gap between textbook economics (which assumes equilibrium) and behavioral/experimental economics (which studies processes).

---

## License

See [LICENSE](LICENSE) file for details.

---

## Getting Help

- **Bugs or Issues?** Check `logs/telemetry.db` (SQLite) for detailed tick-by-tick execution traces
- **Architecture Questions?** See [Technical Manual](docs/1_technical_manual.md)
- **Protocol Details?** Look at protocol source code (heavily commented) and corresponding tests
- **Scenario Issues?** Review [Comprehensive Scenario Template](docs/structures/comprehensive_scenario_template.yaml)

