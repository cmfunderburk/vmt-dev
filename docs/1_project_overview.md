# OUTDATED -- NEEDS A THOROUGH REWRITE
# SEE docs/planning_thinking_etc/BIGGEST_PICTURE/opus_plan for updated thinking
# VMT - Visualizing Microeconomic Theory

**A spatial agent-based simulation investigating how market phenomena emerge from micro-level interactions.**

> **Core Research/Pedagogical Question:** Under what institutional conditions do market-like phenomena actually emerge from individual agent behaviors?

Rather than assuming equilibrium prices exist and agents take them as given, VMT demonstrates how markets form (or fail to form) through explicit institutional mechanisms—search protocols, matching algorithms, and bargaining rules. Agents with heterogeneous preferences forage for resources on a spatial grid and discover exchange opportunities through bilateral negotiation, with prices emerging endogenously from their interactions.

**For the complete strategic vision and research agenda, see:** [`docs/BIGGEST_PICTURE/vision_and_architecture.md`](BIGGEST_PICTURE/vision_and_architecture.md)

---

## Philosophy: Markets as Emergent Phenomena

Traditional economics education jumps quickly from individual agents to abstract equilibrium concepts, treating markets and prices as given primitives. VMT inverts this approach:

**Standard Economics:** Utility → Demand → Market Clearing → Equilibrium Price *(assumed to exist/be supported by some ill-defined institutions)*

**VMT Approach:** Utility → MRS → Reservation Prices → **Search** → **Matching** → **Bargaining** → Trade → *Observed Exchange Ratios*

The middle steps—search, matching, and bargaining—are **explicit institutional mechanisms** that may or may not produce price convergence. This enables:

- **Institutional Comparison:** Different protocols produce different market outcomes
- **Emergence Analysis:** When do bilateral negotiations converge to uniform prices?
- **Pedagogical Clarity:** Markets don't "just happen"—they require specific institutions
- **Research Applications:** Systematic study of market formation conditions

---

## Quick Start

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

##  Protocol Architecture (Phase 1 Complete!)

VMT implements a **modular protocol system** where institutional rules are swappable components:

### Current Status (October 2025)
✅ **Phase 1 Complete:** Protocol architecture implemented with legacy adapters  
✅ **Production Ready:** Spatial foraging, bilateral barter trade  
🚀 **Next:** Alternative protocol implementation (Phase 2a starting)

### Implemented Architecture
- **Legacy Protocols:** Distance-based search, three-pass matching, compensating block bargaining
- **Effect-Based Architecture:** Protocols produce declarative effects applied to state
- **WorldView Pattern:** Immutable snapshots for protocol decisions
- **Full Determinism:** Reproducible simulations with seeded randomness

### Planned Protocol Library (70-90 hour roadmap)
**Phase 2a: Baselines** (8-10 hours)
- Random Walk Search, Random Matching, Split-the-Difference Bargaining

**Phase 3: Centralized Markets** ⭐ **KEY MILESTONE** (25-30 hours)
- Walrasian Auctioneer, Posted-Price Market, Continuous Double Auction
- *Enables core research: Do bilateral prices converge to centralized equilibrium?*

**Phase 4-5: Advanced Mechanisms** (35-45 hours)
- Memory-Based Search, Stable Matching (Gale-Shapley), Nash Bargaining
- Rubinstein Alternating Offers, Network Formation, Auction Mechanisms

**See:** [`docs/protocols_10-27/master_implementation_plan.md`](protocols_10-27/master_implementation_plan.md) for detailed specifications

---

## Features

### Economic Systems
- **CES Utility Functions** - Constant elasticity of substitution (including Cobb-Douglas)
- **Linear Utility Functions** - Perfect substitutes
- **Quadratic Utility Functions** - Bliss points and satiation behavior
- **Translog Utility Functions** - Flexible second-order approximation for empirical work
- **Stone-Geary Utility Functions** - Subsistence constraints and hierarchical needs (LES foundation)
- **Pure Barter Economy** - Direct good-for-good (A↔B) exchanges only
- **Trade Pairing** - Three-pass algorithm with mutual consent and surplus-based fallback
- **Price Search Algorithm** - Finds mutually beneficial prices despite integer rounding
- **Reservation Pricing** - True economic reservation prices (zero bid-ask spread default)

### Behavioral Systems
- **🌾 Foraging** - Distance-discounted utility-seeking movement
- **🏷️ Resource Claiming** - Agents claim forage targets to reduce clustering (enabled by default)
- **♻️ Resource Regeneration** - Sustainable resource management with cooldowns
- **🤝 Trade Pairing** - Agents form committed bilateral partnerships until opportunities exhausted
- **⏰ Trade Cooldown** - Prevents futile re-targeting when trades impossible
- **🎯 Partner Selection** - Distance-discounted surplus ranking with three-pass pairing algorithm

### Technical
- **🎮 Pygame Visualization** - Interactive real-time rendering with smart co-location and target arrows
- **🖥️ GUI Launcher** - Browse scenarios and create custom ones through forms
- **⚡ CLI Scenario Generator** - Generate valid scenarios in < 0.1s with random parameters
- **📊 SQLite Telemetry** - High-performance database logging with interactive PyQt6 viewer
- **🎯 Deterministic** - Same seed → identical results every time
- **⚙️ YAML Configuration** - Easy scenario customization (manual, GUI, or CLI)

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

VMT uses a **SQLite database** (`./logs/telemetry.db`) for all logging.

### Database Schema

The telemetry database includes comprehensive tables:
- **`simulation_runs`** — Run metadata and configuration
- **`agent_snapshots`** — Per-tick agent state (position, inventory, utility, quotes)
- **`trades`** — Successful barter trades with exchange quantities and surplus decomposition
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
- Visualize trade attempts and statistics with pairing context
- Filter by pairing status and trade type
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

## Creating Custom Scenarios

### Current Recommended Workflow: Manual YAML Creation

**The canonical method for creating scenarios is to use the templates and examples in [`docs/structures/`](docs/structures/):**

1. **Browse Templates:**
   - [`minimal_working_example.yaml`](docs/structures/minimal_working_example.yaml) - Simplest valid scenario
   - [`comprehensive_scenario_template.yaml`](docs/structures/comprehensive_scenario_template.yaml) - All parameters documented
   - [`parameter_quick_reference.md`](docs/structures/parameter_quick_reference.md) - Parameter documentation

2. **Copy and Modify:**
   ```bash
   # Copy a template
   cp docs/structures/minimal_working_example.yaml scenarios/my_scenario.yaml
   
   # Edit with your preferred editor
   vim scenarios/my_scenario.yaml  # or code, nano, etc.
   ```

3. **Review Examples:**
   - Check `scenarios/demos/` for annotated pedagogical scenarios
   - Review `scenarios/test/` for specific feature demonstrations
   - See existing scenarios for parameter combinations that work well

**Note:** CLI and GUI scenario generation tools were removed (2025-10-27) as they were outdated. Manual YAML editing with templates is the canonical workflow.

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

## 💱 Trade System

**VMT is a pure barter economy.** All trades are direct A↔B exchanges.

### Configuration Example

#### Barter Economy (A↔B trades)
```yaml
initial_inventories:
  A: { uniform_int: [5, 15] }
  B: { uniform_int: [5, 15] }

utilities:
  mix:
    - weight: 1.0
      type: "ces"
      sigma: 0.5  # Complementary goods
```

See [Technical Manual](./2_technical_manual.md) and [Type Specification](./4_typing_overview.md) for complete details.

---

## 🎓 Academic Use & Key Research Themes

This project makes 'institutional' details, like bargaining protocols/price discovery mechanisms, explicit:

### Research Applications
- **Price Convergence Conditions:** When do exchange ratios converge to uniform "prices"?
- **Bilateral vs Centralized:** When does decentralized exchange approximate Walrasian equilibrium?
- **Institutional Details:** How do specific protocol features affect market outcomes?
- **Spatial Dynamics:** How do search costs and market thickness affect efficiency?

### Pedagogical Features
- **Markets as Constructions:** Students see markets built from institutional rules
- **Comparative Analysis:** Different protocols produce visibly different outcomes
- **Observable Convergence:** Watch price formation (or dispersion) tick-by-tick
- **No Assumptions:** Price-taking emerges (or doesn't) from mechanisms, not axioms
- **Spatial Reasoning:** Information frictions and search costs are endogenous

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

VMT includes comprehensive documentation organized by audience and purpose:

### Strategic Vision & Research
- **[Vision and Architecture](./BIGGEST_PICTURE/vision_and_architecture.md)** - Core philosophy, research agenda, and long-term vision
- **[Protocol Implementation Plan](./protocols_10-27/master_implementation_plan.md)** - 5-phase roadmap for 18+ protocols
- **[Protocol Review](./protocols_10-27/protocol_implementation_review.md)** - Economic and pedagogical analysis

### Technical Documentation
- **[Project Overview](./1_project_overview.md)** (this document) - Quick start and feature overview
- **[Technical Manual](./2_technical_manual.md)** - Detailed implementation, algorithms, and system design
- **[Enhancement Backlog](./3_enhancement_backlog.md)** - Collection of improvement ideas and quality-of-life enhancements
- **[Type Specifications](./4_typing_overview.md)** - Language-agnostic type contracts and data schemas
- **[Scenario Configuration Guide](./scenario_configuration_guide.md)** - Complete reference for creating YAML scenarios

### Getting Started
- **Understanding the vision?** Read [Vision and Architecture](./BIGGEST_PICTURE/vision_and_architecture.md)
- **New to VMT?** Start here and run `python launcher.py`
- **Creating scenarios?** See [Scenario Configuration Guide](./scenario_configuration_guide.md)
- **Implementing protocols?** Check [Protocol Implementation Plan](./protocols_10-27/master_implementation_plan.md)
- **Analyzing data?** Review [Type Specifications](./4_typing_overview.md) for telemetry schema

### Demo Scenarios

The `scenarios/demos/` directory contains annotated pedagogical scenarios demonstrating different exchange patterns and institutional mechanisms. See `scenarios/demos/README.md` for current scenario descriptions.
