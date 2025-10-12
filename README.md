# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-55%2F55%20passing-brightgreen)]()
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

## 🌟 Key Achievement

**Agents with complementary preferences now successfully trade, forage sustainably, and exhibit realistic economic behavior.**

This system overcame fundamental challenges in bridging continuous economic theory (marginal rates of substitution) with discrete implementation constraints (integer trades, tick-based time), resulting in a pedagogically clear and economically sound simulation.

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
- **📊 Enhanced Telemetry** - Logs every decision, trade attempt, and state change
- **🎯 Deterministic** - Same seed → identical results every time
- **⚙️ YAML Configuration** - Easy scenario customization
- **⚡ Performance Optimized** - O(N) agent interactions via spatial indexing

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

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_resource_regeneration.py -v

# With coverage
pytest tests/ --cov=vmt_engine --cov-report=html
```

---

## 📖 Documentation

### Primary Documentation
- **[Planning-Post-v1.md](PLANS/Planning-Post-v1.md)** - Complete authoritative specification
- **[V1_CHECKPOINT_REVIEW.md](PLANS/V1_CHECKPOINT_REVIEW.md)** - Implementation retrospective
- **[Big_Review.md](PLANS/Big_Review.md)** - Comprehensive evaluation

### System Documentation
- [TELEMETRY_IMPLEMENTATION.md](PLANS/docs/TELEMETRY_IMPLEMENTATION.md) - Enhanced logging system
- [PRICE_SEARCH_IMPLEMENTATION.md](PLANS/docs/PRICE_SEARCH_IMPLEMENTATION.md) - Price discovery algorithm
- [TRADE_COOLDOWN_IMPLEMENTATION.md](PLANS/docs/TRADE_COOLDOWN_IMPLEMENTATION.md) - Cooldown mechanics
- [RESOURCE_REGENERATION_IMPLEMENTATION.md](PLANS/docs/RESOURCE_REGENERATION_IMPLEMENTATION.md) - Regeneration system
- [CONFIGURATION.md](PLANS/docs/CONFIGURATION.md) - Parameter reference

---

## 🎯 Example Usage

### Python API

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

# Analyze logs
import pandas as pd
trades = pd.read_csv("logs/trades.csv")
print(f"Total trades: {len(trades)}")
print(f"Average trade size: {trades['dA'].mean():.2f}")
```

### Example Output

```
Agent 0: A=6, B=6, U=1.50
Agent 1: A=6, B=6, U=1.50
Agent 2: A=6, B=6, U=1.50
Total trades: 12
Average trade size: 1.25
```

---

## 🏗️ Architecture

### Project Structure

```
vmt-dev/
├── vmt_engine/              # Core simulation engine
│   ├── core/                # State structures
│   │   ├── state.py         # Inventory, Quote, Position
│   │   ├── grid.py          # Grid and Resource management
│   │   ├── agent.py         # Agent representation
│   │   └── spatial_index.py # Spatial hash for O(N) proximity queries
│   ├── econ/                # Economic utilities
│   │   └── utility.py       # UCES, ULinear, base interface
│   ├── systems/             # Subsystems
│   │   ├── perception.py    # Vision and neighbor detection
│   │   ├── movement.py      # Pathfinding and targeting
│   │   ├── foraging.py      # Harvesting and regeneration
│   │   ├── quotes.py        # Quote generation
│   │   └── matching.py      # Trade matching and price search
│   └── simulation.py        # Main simulation loop
├── vmt_launcher/            # GUI Launcher
│   ├── launcher.py          # Main launcher window
│   ├── scenario_builder.py  # Custom scenario creator
│   └── validator.py         # Input validation
├── telemetry/               # Logging and diagnostics
│   ├── logger.py            # Trade logging
│   ├── snapshots.py         # State snapshots
│   ├── decision_logger.py   # Decision tracking
│   └── trade_attempt_logger.py  # Trade diagnostics
├── scenarios/               # Configuration
│   ├── schema.py            # ScenarioConfig dataclasses
│   ├── loader.py            # YAML parsing
│   ├── single_agent_forage.yaml
│   └── three_agent_barter.yaml
├── vmt_pygame/              # Visualization
│   └── renderer.py          # Pygame rendering
├── tests/                   # Test suite (55 tests)
│   ├── test_core_state.py
│   ├── test_utility_ces.py
│   ├── test_utility_linear.py
│   ├── test_resource_regeneration.py
│   ├── test_trade_cooldown.py
│   ├── test_performance.py  # Performance benchmarks
│   └── ... (and more)
├── PLANS/                   # Documentation
│   ├── Planning-Post-v1.md  # Main specification
│   └── docs/                # System docs
├── launcher.py              # GUI entry point
└── main.py                  # CLI entry point
```

### Tick Structure

Each simulation tick executes 7 phases in order:

1. **Perception** - Observe neighbors, quotes, resources
2. **Decision** - Choose trading partners or foraging targets
3. **Movement** - Move toward targets
4. **Trade** - Execute one trade per pair
5. **Foraging** - Harvest resources
6. **Resource Regeneration** - Regenerate depleted resources (with cooldown)
7. **Housekeeping** - Refresh quotes, log telemetry

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
   - **Utility Functions**: Add multiple utility types with custom parameters
4. **Click "Generate Scenario"**
5. **Save the YAML file** (default: `scenarios/` folder)
6. **New scenario automatically appears** in the launcher list

### Utility Function Options

#### CES Utility
- **rho** (ρ): Elasticity parameter (ρ ≠ 1)
  - ρ → 0: Cobb-Douglas (U = A^wA × B^wB)
  - ρ < 0: Complements (prefer balanced bundles)
  - ρ > 0: Substitutes (more flexible trade-offs)
- **wA, wB**: Preference weights (must be positive)

#### Linear Utility
- **vA, vB**: Value coefficients (U = vA×A + vB×B)
- Perfect substitutes with constant MRS = vA/vB

### Tips for Good Scenarios

- **Grid Size**: 20-50 works well for visualization
- **Agent Count**: 3-20 for educational demos, 50+ for experiments
- **Vision Radius**: Should be ≥ interaction radius
- **Resource Density**: 0.1-0.3 provides good scarcity
- **Trade Cooldown**: 5-10 ticks prevents infinite retries
- **Utility Mix**: Use complementary preferences for interesting trades

---

## ⚙️ Configuration

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

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `spread` | 0.0 | Bid-ask spread (critical: keep at 0.0 for CES) |
| `trade_cooldown_ticks` | 5 | Ticks after failed trade before retry |
| `resource_growth_rate` | 0 | Resource regeneration rate (0 = disabled) |
| `resource_regen_cooldown` | 5 | Ticks after harvest before regeneration |
| `vision_radius` | 5 | Agent perception range |
| `beta` | 0.95 | Discount factor for foraging decisions |

See [CONFIGURATION.md](PLANS/docs/CONFIGURATION.md) for complete parameter reference.

---

## 🔬 Testing

### Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| Core State | 5 | Grid, inventory, agent management |
| Utilities | 12 | CES, Linear, edge cases |
| Scenarios | 3 | YAML loading and validation |
| Simulation | 4 | Initialization and determinism |
| Foraging | 3+ | Movement, harvesting, utility-seeking |
| Regeneration | 8 | Cooldown, growth, caps |
| Trade Cooldown | 4 | Partner filtering, expiry |
| Trade Rounding | 2 | Compensating multi-lot |
| Reservations | 5 | Zero-safe bounds |
| **Total** | **45** | **All passing** ✅ |

### Running Tests

```bash
# All tests with verbose output
pytest tests/ -v

# Fast mode (no verbose)
pytest tests/

# Specific category
pytest tests/test_resource_regeneration.py -v

# With coverage report
pytest tests/ --cov=vmt_engine --cov-report=term-missing

# Stop on first failure
pytest tests/ -x
```

---

## 📊 Telemetry & Analysis

### Log Files (in `logs/` directory)

| File | Content | Frequency |
|------|---------|-----------|
| `trades.csv` | Successful trades | Every trade |
| `trade_attempts.csv` | All trade attempts (including failures) | Every attempt |
| `agent_snapshots.csv` | Agent states | Every tick |
| `decisions.csv` | Partner selection and movement | Every tick |
| `resource_snapshots.csv` | Resource states | Periodic |

### Analysis Example

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load logs
trades = pd.read_csv("logs/trades.csv")
agents = pd.read_csv("logs/agent_snapshots.csv")

# Analyze trade volume over time
trades_per_tick = trades.groupby('tick').size()
plt.plot(trades_per_tick)
plt.xlabel('Tick')
plt.ylabel('Trades')
plt.title('Trade Volume Over Time')
plt.show()

# Track utility convergence
for agent_id in agents['agent_id'].unique():
    agent_data = agents[agents['agent_id'] == agent_id]
    plt.plot(agent_data['tick'], agent_data['U'], label=f'Agent {agent_id}')
plt.xlabel('Tick')
plt.ylabel('Utility')
plt.legend()
plt.title('Utility Convergence')
plt.show()
```

---

## 🎓 Key Insights & Design Principles

### 1. The MRS vs. Discrete Trade Gap

**Challenge:** Continuous economic theory (marginal rates of substitution) doesn't guarantee discrete integer trades will succeed.

**Solution:** Price search algorithm tries multiple candidates within the valid [ask, bid] range until finding terms that work with integer rounding.

### 2. Bootstrap Requirement for CES

**Challenge:** CES utilities with extreme inventory imbalances produce unusable prices.

**Solution:** Bootstrap agents with non-zero, somewhat balanced inventories (e.g., [8,4] and [4,8], not [10,0] and [0,10]).

### 3. Cooldowns Prevent Pathologies

**Pattern:** Both trade and resource cooldowns follow `action → wait → allow_again` to prevent loops.

**Applications:**
- Trade cooldown prevents futile re-targeting of impossible trades
- Resource cooldown creates spatial foraging strategies

### 4. Telemetry-Driven Development

**Principle:** Log failures, not just successes. Most bugs manifest as invisible failures.

**Implementation:** Every trade attempt, decision, and state change is logged with diagnostic information.

---

## 🚨 Troubleshooting

### Agents Not Trading

**Symptoms:** Positive surplus detected but no trades executed.

**Common Causes:**
1. **Inventory too imbalanced** - Bootstrap with [8,4,6] and [4,8,6], not [10,0,0]
2. **Spread too high** - Use `spread: 0.0` (not 0.05) for CES utilities
3. **Integer rounding issues** - Check `trade_attempts.csv` for "no_block_found" failures

**Debug:**
```bash
# Check trade attempts
grep "Agent" logs/trade_attempts.csv | head -20

# Check if agents are targeting each other
grep "partner" logs/decisions.csv | head -20
```

### Resources Not Regenerating

**Symptoms:** Resources stay depleted forever.

**Common Causes:**
1. **Regeneration disabled** - Set `resource_growth_rate: 1` (not 0)
2. **Cooldown not expired** - Wait `resource_regen_cooldown` ticks after harvest
3. **Never-harvested cells** - Only initially-seeded cells regenerate

**Debug:**
```bash
# Check resource state
grep "A\|B" logs/resource_snapshots.csv | tail -50
```

### Tests Failing

**Symptoms:** `pytest` shows failures.

**Common Causes:**
1. **Dependencies missing** - Run `pip install -r requirements.txt`
2. **Python version** - Requires Python 3.11+
3. **Modified core logic** - Review critical production rules in Planning-Post-v1.md Appendix B

**Debug:**
```bash
# Run single failing test with verbose output
pytest tests/test_failing.py::test_name -v -s

# Check Python version
python --version  # Should be 3.11+
```

---

## 🎯 Production Deployment

### Critical Production Rules

**For maintainers and extenders:**

1. ✅ **Never change `spread` default from 0.0** - CES trading depends on this
2. ✅ **Always log failures, not just successes** - Debugging depends on this
3. ✅ **Test with CES utilities (rho=-0.5)** - Most sensitive to changes
4. ✅ **Bootstrap inventories away from zero** - Especially for CES agents
5. ✅ **Preserve determinism** - Sort by ID, use explicit seeds
6. ✅ **One trade per tick** - Don't reintroduce multi-block loops
7. ✅ **Run full test suite** - All 45 tests must pass

### Performance Notes

- **Grid Size:** O(N²) operations per tick for resource regeneration
- **Typical:** 32×32 grid with 3-10 agents runs at 60+ ticks/second
- **Scaling:** Tested up to 100×100 grids with 50 agents
- **Bottlenecks:** Pygame rendering (disable for faster batch runs)

---

## 🗺️ Roadmap

### Completed ✅
- ✅ CES and Linear utility functions
- ✅ Price search algorithm
- ✅ Resource regeneration with cooldowns
- ✅ Trade cooldown system
- ✅ Enhanced telemetry
- ✅ Pygame visualization
- ✅ 45 comprehensive tests

### Short-term
- [ ] Visualize cooldown states in renderer
- [ ] Add Option 3: random resource spawning
- [ ] Performance profiling dashboard
- [ ] Scenario builder GUI

### Long-term
- [ ] Leontief and Stone-Geary utilities
- [ ] Nash bargaining pricing mechanisms
- [ ] Learning and adaptation
- [ ] Multi-good extension (A, B, C, ...)
- [ ] Cash/credit systems
- [ ] Network/graph-based trade

---

## 📚 Academic Use

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

---

## 🤝 Contributing

This is a research/educational project. Key areas for contribution:

- **New utility functions** (Leontief, Stone-Geary)
- **Alternative pricing mechanisms** (Nash bargaining, learning)
- **Performance optimizations** (Numba, vectorization)
- **Visualization enhancements** (D3.js web version?)
- **Educational materials** (tutorials, exercises, lecture slides)

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black mypy

# Format code
black vmt_engine/ tests/

# Type checking
mypy vmt_engine/

# Run tests with coverage
pytest tests/ --cov=vmt_engine --cov-report=html
```

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

This project successfully bridges continuous economic theory with discrete computational constraints. The journey from "agents not trading" to "production-ready simulation" was enabled by:

1. **Enhanced telemetry** - Making invisible failures visible
2. **Evidence-based iteration** - Discovering problems through testing
3. **Price search innovation** - Solving the MRS/rounding gap
4. **Cooldown mechanisms** - Preventing pathological loops

**Key Lesson:** When something doesn't work, first make it observable. The enhanced logging system was the foundation that enabled all subsequent fixes.

---

## 📞 Contact & Support

- **Documentation:** See `PLANS/` directory for comprehensive specifications
- **Issues:** Review `PLANS/docs/` for known issues and solutions
- **Testing:** Run `pytest tests/ -v` to verify installation

**Status:** Production Ready - 45/45 Tests Passing ✅

---

<p align="center">
  <strong>VMT - Visualizing Microeconomic Theory</strong><br>
  Teaching economics through spatial simulation
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue" />
  <img src="https://img.shields.io/badge/Tests-45%2F45-brightgreen" />
  <img src="https://img.shields.io/badge/Status-Production%20Ready-blue" />
</p>
