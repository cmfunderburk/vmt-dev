# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-54%2B%2F54%2B%20passing-brightgreen)]()
[![Version](https://img.shields.io/badge/version-1.1.0-blue)]()
[![Status](https://img.shields.io/badge/status-production%20ready-blue)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![GUI](https://img.shields.io/badge/GUI-PyQt5-green)]()

**A spatial agent-based simulation for teaching and researching microeconomic behavior through visualization.**

Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral barter trade using reservation-price-based negotiation. The system successfully demonstrates complex economic phenomena including price discovery, gains from trade, and sustainable resource management.

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
| **Q/ESC** | Quit |

---

## ✨ Features

### Economic Systems
- **🎲 CES Utility Functions** - Constant elasticity of substitution (including Cobb-Douglas)
- **📏 Linear Utility Functions** - Perfect substitutes
- **💱 Price Search Algorithm** - Finds mutually beneficial prices despite integer rounding
- **🤝 Bilateral Barter** - One-on-one negotiation with compensating multi-lot rounding
- **📈 Reservation Pricing** - True economic reservation prices (zero bid-ask spread)

### Behavioral Systems
- **🌾 Foraging** - Distance-discounted utility-seeking movement
- **♻️ Resource Regeneration** - Sustainable resource management with cooldowns
- **⏰ Trade Cooldown** - Prevents futile re-targeting when trades impossible
- **🎯 Partner Selection** - Surplus-based matching with mutual improvement checks

### Technical Excellence
- **🔬 55 Passing Tests** - Comprehensive coverage including performance benchmarks
- **🎮 Pygame Visualization** - Interactive real-time rendering
- **🖥️ GUI Launcher** - Browse scenarios and create custom ones through forms
- **📊 SQLite Telemetry** - High-performance database logging with an interactive viewer
- **🎯 Deterministic** - Same seed → identical results every time
- **⚙️ YAML Configuration** - Easy scenario customization
- **⚡ Performance Optimized** - O(N) agent interactions via spatial indexing

---

## 📊 Telemetry & Analysis

As of v1.1, VMT uses a high-performance **SQLite database** for all logging, replacing the legacy CSV system. This results in a ~99% reduction in log file size and enables sub-second data queries.

### Interactive Log Viewer

Use the PyQt5-based log viewer to explore simulation data:

```bash
python view_logs.py
```

The viewer allows you to:
- Scrub through the simulation timeline tick-by-tick.
- Analyze individual agent states, trajectories, and trade histories.
- Visualize trade attempts and statistics.
- Export data to CSV for external analysis.

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

### Using the GUI Builder

The easiest way to create custom scenarios is through the GUI:

1. **Launch the GUI**: `python launcher.py`
2. **Click "Create Custom Scenario"** at the top
3. **Fill in the tabs**:
   - **Basic Settings**: Name, grid size, agents, initial inventories
   - **Simulation Parameters**: Spread, vision, movement, trade parameters
   - **Resources**: Density, growth rate, regeneration cooldown
   - **Utility Functions**: Define a population mix. You can add multiple utility function types (e.g., CES, Linear) with different parameters and weights. Each agent created for the simulation will be randomly assigned *one* of these utility functions according to the specified weights.
4. **Click "Generate Scenario"**
5. **Save the YAML file** (default: `scenarios/` folder)
6. **New scenario automatically appears** in the launcher list

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
