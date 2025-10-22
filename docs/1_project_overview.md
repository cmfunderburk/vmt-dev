# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-316%2B%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green)]()

**A spatial agent-based simulation for teaching and researching microeconomic behavior through visualization.**

Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral trade (barter or monetary exchange) using reservation-price-based negotiation. The system demonstrates complex economic phenomena including price discovery, gains from trade, pairing dynamics, and sustainable resource management.

<p align="center">
  <img src="https://img.shields.io/badge/🎯-Agents%20Successfully%20Trading-success" />
  <img src="https://img.shields.io/badge/♻️-Sustainable%20Foraging-success" />
  <img src="https://img.shields.io/badge/📊-Enhanced%20Telemetry-success" />
</p>

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
cd vmt-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run a Simulation

#### Option 1: GUI Launcher (Recommended)

```bash
# Launch the GUI
python launcher.py
```

The GUI launcher provides:
- 📋 **Browse Scenarios** - See all available `.yaml` files
- 🎲 **Easy Seed Entry** - Simple integer input field
- ✨ **Create Custom Scenarios** - Build scenarios through forms (no YAML editing)
- 📖 **Built-in Documentation** - In-context help for utility function parameters
- ▶️ **One-Click Launch** - Run simulations with a button press

#### Option 2: Command Line

```bash
# Run with visualization
python main.py scenarios/three_agent_barter.yaml 42

# Run with different seed
python main.py scenarios/single_agent_forage.yaml 123
```

### Interactive Controls

| Key | Action |
|-----|--------|
| **Space** | Pause/Resume |
| **S** | Single step (when paused) |
| **R** | Reset simulation |
| **+/-** | Adjust speed |
| **T** | Toggle target arrows (show agent targets and pairings) |
| **Q/ESC** | Quit |

---

## ✨ Features

### Economic Systems
- **🎲 CES Utility Functions** - Constant elasticity of substitution (including Cobb-Douglas)
- **📏 Linear Utility Functions** - Perfect substitutes
- **🎯 Quadratic Utility Functions** - Bliss points and satiation behavior
- **📊 Translog Utility Functions** - Flexible second-order approximation for empirical work
- **🏠 Stone-Geary Utility Functions** - Subsistence constraints and hierarchical needs (LES foundation)
- **💱 Generic Matching Algorithm** - Supports barter (A↔B) and monetary exchange (A↔M, B↔M)
- **💰 Money System (v1.0)** - Complete monetary economics simulation
  - Four exchange regimes: `barter_only`, `money_only`, `mixed`, `mixed_liquidity_gated`
  - Two money modes: `quasilinear` (simple) and `kkt_lambda` (advanced)
  - Money-first tie-breaking in mixed economies
  - Mode × regime interaction for temporal control
  - Rich telemetry and analysis tools
- **🤝 Trade Pairing** - Three-pass algorithm with mutual consent and surplus-based fallback
- **💱 Price Search Algorithm** - Finds mutually beneficial prices despite integer rounding
- **📈 Reservation Pricing** - True economic reservation prices (zero bid-ask spread default)

### Behavioral Systems
- **🌾 Foraging** - Distance-discounted utility-seeking movement
- **🏷️ Resource Claiming** - Agents claim forage targets to reduce clustering (enabled by default)
- **♻️ Resource Regeneration** - Sustainable resource management with cooldowns
- **🤝 Trade Pairing** - Agents form committed bilateral partnerships until opportunities exhausted
- **⏰ Trade Cooldown** - Prevents futile re-targeting when trades impossible
- **🎯 Partner Selection** - Distance-discounted surplus ranking with three-pass pairing algorithm

### Technical Excellence
- **🔬 316+ Passing Tests** - Comprehensive coverage including pairing, money system, and performance benchmarks
- **🎮 Pygame Visualization** - Interactive real-time rendering with smart co-location and target arrows
- **🖥️ GUI Launcher** - Browse scenarios and create custom ones through forms
- **⚡ CLI Scenario Generator** - Generate valid scenarios in < 0.1s with random parameters
- **📊 SQLite Telemetry** - High-performance database logging with interactive PyQt6 viewer
- **🎯 Deterministic** - Same seed → identical results every time
- **⚙️ YAML Configuration** - Easy scenario customization (manual, GUI, or CLI)
- **⚡ Performance Optimized** - O(N) agent interactions via spatial indexing and trade pairing

### Visualization Features
- **🎯 Target Arrows** - Press **T** to toggle visualization of agent targets and pairings:
  - Shows which agents are targeting each other for trade
  - Highlights paired agents with distinct arrow colors
  - Displays forage targets with resource-colored arrows
  - Helps understand decision-making and commitment dynamics
- **👥 Smart Co-location Rendering** - When multiple agents occupy the same cell, they are automatically rendered with:
  - Scaled-down sprites proportional to agent count (2 agents = 75% size, 3 = 60%, etc.)
  - Non-overlapping geometric layouts (diagonal for 2, triangle for 3, corners for 4, circle pack for 5+)
  - Organized inventory labels that remain readable
  - Pure visualization enhancement - simulation positions remain accurate for telemetry
- **📍 Visual Clarity** - Co-located agents are always distinguishable, making trades and resource competition easy to observe
- **🎨 Color-Coded Agents** - Green for CES, Purple for Linear, Blue for Quadratic, Orange for Translog, Red for Stone-Geary
- **📊 Real-Time HUD** - Displays tick counter, agent count, total inventory, and recent trades

---

## 📊 Telemetry & Analysis

VMT uses a high-performance **SQLite database** (`./logs/telemetry.db`) for all logging. This results in a ~99% reduction in log file size compared to legacy CSV systems and enables sub-second data queries.

### Database Schema

The telemetry database includes comprehensive tables:
- **`simulation_runs`** — Run metadata with exchange_regime, money_mode
- **`agent_snapshots`** — Per-tick agent state (position, inventory, utility, quotes, lambda)
- **`trades`** — Successful trades with exchange pair type, money transfers, surplus decomposition
- **`decisions`** — Agent decision outcomes with pairing status
- **`pairings`** — Pairing/unpairing events with reason codes
- **`preferences`** — Agent preference rankings (top 3 by default)
- **`tick_states`** — Per-tick mode and regime state
- **`resource_snapshots`** — Grid resource state over time

### Interactive Log Viewer

Use the PyQt6-based log viewer to explore simulation data:

```bash
python view_logs.py
```

The viewer allows you to:
- Scrub through the simulation timeline tick-by-tick
- Analyze individual agent states, trajectories, and trade histories
- Visualize trade attempts and statistics with full money/pairing context
- Filter by exchange regime, pairing status, and trade type
- Export data to CSV for external analysis

### Python API

For programmatic analysis, you can still run simulations and access data directly in Python.

```python
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario

# Load scenario
scenario = load_scenario("scenarios/three_agent_barter.yaml")

# Create simulation with seed
sim = Simulation(scenario, seed=42)

# Run for 100 ticks
sim.run(max_ticks=100)

# Access results
for agent in sim.agents:
    A, B = agent.inventory.A, agent.inventory.B
    U = agent.utility.u(A, B)
    print(f"Agent {agent.id}: A={A}, B={B}, U={U:.2f}")
```

---

## ✨ Creating Custom Scenarios

VMT provides **three methods** for creating scenarios, each optimized for different workflows:

### Method 1: CLI Scenario Generator (Developer Workflow) ⚡

**Best for:** Rapid iteration, test suites, scripting, batch generation

The command-line scenario generator creates valid YAML files in seconds:

```bash
# Basic usage - generates scenarios/my_test.yaml
python3 -m src.vmt_tools.generate_scenario my_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities ces,linear --resources 0.3,5,1 --seed 42

# With presets (Phase 2)
python3 -m src.vmt_tools.generate_scenario demo --preset money_demo

# Money economy (Phase 2)
python3 -m src.vmt_tools.generate_scenario money_test \
  --agents 20 --grid 30 --inventory-range 10,50 \
  --utilities linear --resources 0.3,5,1 \
  --exchange-regime money_only
```

**Current Status: Phase 2 Complete ✅ (2025-10-21)**
- ✅ All 5 utility types with conservative parameter randomization
- ✅ Deterministic generation with `--seed` flag
- ✅ Automatic validation (schema-compliant YAML)
- ✅ Generation time < 0.1 seconds per scenario
- ✅ Exchange regime selection (`--exchange-regime {barter_only|money_only|mixed}`)
- ✅ Scenario presets (`--preset {minimal|standard|large|money_demo|mixed_economy}`)
- ✅ Automatic money inventory generation for monetary economies

**Future Phases (Based on Feedback):**
- 🔮 Phase 3: Weighted utility mixes (`--utilities ces:0.6,linear:0.4`)
- 🔮 Phase 3: Custom money inventory ranges
- 🔮 Phase 3: Parameter validation mode
- 🔮 Phase 3: Unit test integration

See [`docs/guides/scenario_generator.md`](docs/guides/scenario_generator.md) for complete guide.

### Method 2: GUI Builder (Interactive)

**Best for:** Exploration, one-off scenarios, learning

The graphical scenario builder provides a form-based interface:

1. **Launch the GUI**: `python launcher.py`
2. **Click "Create Custom Scenario"** at the top
3. **Fill in the tabs**:
   - **Basic Settings**: Name, grid size, agents, initial inventories
   - **Simulation Parameters**: Spread, vision, movement, trade parameters
   - **Resources**: Density, growth rate, regeneration cooldown
   - **Utility Functions**: Define a population mix. You can add multiple utility function types (CES, Linear, Quadratic, Translog, Stone-Geary) with different parameters and weights. Each agent created for the simulation will be randomly assigned *one* of these utility functions according to the specified weights.
4. **Click "Generate Scenario"**
5. **Save the YAML file** (default: `scenarios/` folder)
6. **New scenario automatically appears** in the launcher list

### Method 3: Manual YAML Editing (Advanced)

**Best for:** Fine-grained control, advanced features, documentation

### Scenario Example

```yaml
schema_version: 1
name: three_agent_barter
N: 32  # Grid size (32×32)
agents: 3

initial_inventories:
  A: [8, 4, 6]  # Per-agent initial A
  B: [4, 8, 6]  # Per-agent initial B

utilities:
  mix:
    - type: ces
      weight: 1.0
      params:
        rho: -0.5    # Complementarity
        wA: 1.0
        wB: 1.0

params:
  # Trading
  spread: 0.0                    # Bid-ask spread (0 = true reservation prices)
  trade_cooldown_ticks: 5        # Cooldown after failed trade
  
  # Resources
  resource_growth_rate: 1        # Units regenerating per tick
  resource_regen_cooldown: 5     # Ticks to wait after harvest
  
  # Foraging
  vision_radius: 5               # Perception range
  forage_rate: 1                 # Units harvested per tick
  beta: 0.95                     # Time discount factor

resource_seed:
  density: 0.15                  # Fraction of cells with resources
  amount: 3                      # Initial resource amount
```

---

## 🏷️ Resource Claiming

**Enabled by default** (`enable_resource_claiming: true`), the resource claiming system coordinates agent foraging to reduce inefficient clustering:

- **Claiming Mechanism**: During the Decision phase, agents **claim** forage targets by recording `resource_claims[position] = agent_id`
- **Claim Filtering**: Other agents see claimed resources as unavailable and select alternatives
- **Deterministic**: Lower-ID agents claim resources first (processed in ID order)
- **Stale Clearing**: Claims expire when agents reach the resource or change targets
- **Single-Harvester**: Only the first agent (by ID) at a cell harvests per tick (`enforce_single_harvester: true`)
- **Benefits**: Reduces clustering; increases spatial distribution; improves resource utilization

See [Technical Manual](./2_technical_manual.md#resource-claiming-system) for implementation details.

---

## 💰 Money System (Phases 1-2)

VMT implements a money system with **quasilinear utility** and configurable **exchange regimes**:

### Exchange Regimes

The `exchange_regime` parameter controls allowed exchange types:
- **`"barter_only"`** (default) — Only A↔B trades; backward compatible with legacy scenarios
- **`"money_only"`** — Only A↔M and B↔M trades (goods for money)
- **`"mixed"`** — All exchange pairs allowed; generic matching selects highest-surplus pair

### Quasilinear Utility

U_total = U_goods(A, B) + λ·M

Where:
- **U_goods** — Utility from goods (CES, Linear, Quadratic, Translog, or Stone-Geary)
- **λ** (`lambda_money`) — Marginal utility of money (default: 1.0)
- **M** — Money holdings in minor units (e.g., cents)

### Configuration Example

```yaml
initial_inventories:
  A: { uniform_int: [5, 15] }
  B: { uniform_int: [5, 15] }
  M: 100  # Give each agent 100 units of money

params:
  exchange_regime: "mixed"         # Allow all exchange types
  money_mode: "quasilinear"        # Fixed lambda (Phases 1-2)
  money_scale: 1                   # Minor units scale
  lambda_money: 1.0                # Marginal utility of money
```

### Telemetry

Money trades are logged with full context:
- **`trades.dM`** — Money transfer amount
- **`trades.exchange_pair_type`** — "A<->B", "A<->M", "B<->M"
- **`trades.buyer_lambda`**, **`trades.seller_lambda`** — Lambda values at trade time
- **`tick_states.active_pairs`** — JSON array of active exchange pairs per tick

See [Technical Manual](./2_technical_manual.md#money-system-phases-1-2) and [Type Specification](./4_typing_overview.md#7-money--market-contracts) for complete details.

---

## 🎓 Academic Use & Key Concepts

This simulation is designed for **teaching microeconomic theory** through visualization. Key pedagogical features:

- **Observable Convergence:** Watch agents reach equilibrium step-by-step
- **Edgeworth Box Dynamics:** Visualize gains from trade spatially
- **Price Discovery:** See how reservation prices lead to mutually beneficial terms
- **Resource Economics:** Demonstrate sustainable vs. extractive strategies
- **Heterogeneous Preferences:** Show how different utility functions interact

### Suggested Exercises

1. **Vary complementarity** - Change CES `rho` from -2 to +2, observe trading patterns
2. **Bootstrap experiments** - Compare [10,0] vs [8,2] initial inventories
3. **Regeneration rates** - Test sustainable foraging with different `resource_growth_rate`
4. **Cooldown tuning** - How does `trade_cooldown_ticks` affect exploration?
5. **Mixed populations** - Combine CES and Linear agents, analyze welfare

### New Utility Function Demonstrations

The following scenarios demonstrate the three new utility functions:

1. **bliss_point_demo.yaml** - Quadratic utility with agents seeking optimal (bliss point) inventories
   - Demonstrates satiation behavior and non-monotonic preferences
   - Agents refuse trades when inventories exceed bliss points

2. **translog_estimation_demo.yaml** - Mixed population with Translog and CES utilities
   - Shows variable elasticity of substitution across inventory levels
   - Useful for empirical estimation exercises and functional form comparisons

3. **subsistence_economy_demo.yaml** - Stone-Geary utility with subsistence constraints
   - Demonstrates desperate trading when agents are close to subsistence
   - Shows market segmentation between subsistence and normal traders
   - Models basic needs vs. discretionary consumption

4. **mixed_utility_showcase.yaml** - All three new utilities in a heterogeneous population
   - Demonstrates architectural flexibility
   - Rich diversity of trading patterns and economic behaviors

---

## 📚 Documentation

VMT includes comprehensive documentation for developers, researchers, and users:

### Core Documentation

- **[Project Overview](./1_project_overview.md)** (this document) - Quick start, features, and high-level architecture
- **[Technical Manual](./2_technical_manual.md)** - Detailed implementation, algorithms, and system design
- **[Scenario Configuration Guide](./scenario_configuration_guide.md)** - Complete reference for creating YAML scenarios
- **[Type Specifications](./4_typing_overview.md)** - Language-agnostic type contracts and data schemas
- **[Strategic Roadmap](./3_strategic_roadmap.md)** - Future plans and enhancement priorities

### Getting Started

- **New to VMT?** Start with [Project Overview](./1_project_overview.md) and run `python launcher.py`
- **Creating scenarios?** See [Scenario Configuration Guide](./scenario_configuration_guide.md)
- **Understanding internals?** Read [Technical Manual](./2_technical_manual.md)
- **Analyzing data?** Check [Type Specifications](./4_typing_overview.md) for telemetry schema

### Demo Scenarios

The `scenarios/demos/` directory contains annotated pedagogical scenarios:

1. **demo_01_simple_money.yaml** - Why money? (double coincidence of wants)
2. **demo_02_barter_vs_money.yaml** - Direct comparison of exchange systems
3. **demo_03_mixed_regime.yaml** - Hybrid economy (barter + money coexistence)
4. **demo_04_mode_schedule.yaml** - Temporal control (forage/trade cycles)
5. **demo_05_liquidity_zones.yaml** - Market thickness and spatial variation
6. **demo_06_money_aware_pairing.yaml** - Money-aware pairing mechanics
