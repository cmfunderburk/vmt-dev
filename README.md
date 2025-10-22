# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-316%2B%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green)]()

A spatial agent-based simulation for teaching and researching microeconomic behavior through visualization.

Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral trade (barter or monetary exchange) using reservation-price-based negotiation.

---

## Current Implementation Status

### ✅ **Fully Implemented & Working**
- **Core 7-Phase Simulation Engine** - Deterministic simulation loop with perception, decision, movement, trade, forage, regeneration, and housekeeping phases
- **5 Utility Functions** - CES, Linear, Quadratic, Translog, Stone-Geary with full parameter support
- **Money System** - Quasilinear utility with heterogeneous λ values for realistic monetary trading
- **Exchange Regimes** - `barter_only`, `money_only`, `mixed` (all trade types)
- **Spatial Dynamics** - Vision radius, movement budgets, resource claiming, foraging
- **Mode Scheduling** - Temporal control with global cycle patterns
- **PyQt6 GUI** - Scenario browser, launcher, and log viewer
- **SQLite Telemetry** - Comprehensive logging system with 99% compression over CSV
- **316+ Tests** - Comprehensive test coverage with deterministic validation

### 🔄 **Planned Features (Not Yet Implemented)**
- **KKT Lambda Mode** - Endogenous λ estimation from market prices
- **Mixed Liquidity Gated** - Barter fallback when money market is thin
- **Distribution Syntax** - Random inventory generation
- **Advanced Mode Scheduling** - Agent-specific and spatial zone patterns

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone and navigate to the repository
cd vmt-dev

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run Your First Simulation

**Launch the GUI (recommended):**

```bash
python launcher.py
```

The launcher provides an intuitive interface to:
- Browse and select pre-built scenario files
- Configure simulation parameters (seed, step limits)
- Create custom scenarios without editing YAML
- Run simulations with real-time visualization

**Try a demo scenario:**
1. Launch the GUI
2. Select `scenarios/demos/demo_01_foundational_barter.yaml`
3. Click "Launch Simulation"
4. Watch agents forage and trade!

### Command-Line Option

For headless runs or scripting:

```bash
python main.py --scenario scenarios/foundational_barter_demo.yaml --seed 42 --max_steps 200
```

---

## Key Features (Currently Implemented)

### **Spatial Agent-Based Simulation**
- **7-Phase Deterministic Engine** - Reproducible simulation with strict phase ordering
- **Spatial Foraging** - Agents move on N×N grid collecting resources
- **Resource Management** - Growth, regeneration, claiming, and depletion mechanics

### **Economic Trading System**
- **Bilateral Trading** - Barter (A↔B) and monetary (A↔M, B↔M) exchange
- **Money-Aware Pairing** - Smart matching algorithm for optimal trade selection
- **Reservation Price Negotiation** - Agents use marginal utility to set bid/ask prices
- **Heterogeneous Preferences** - Agent-specific utility functions and money valuations

### **Rich Utility Functions**
- **CES (Constant Elasticity of Substitution)** - Most flexible, includes Cobb-Douglas
- **Linear** - Perfect substitutes with constant MRS
- **Quadratic** - Bliss point preferences with satiation
- **Translog** - Flexible functional form for empirical estimation
- **Stone-Geary** - Non-homothetic preferences with subsistence constraints

### **Money System**
- **Quasilinear Utility** - U_total = U_goods(A,B) + λ·M
- **Heterogeneous Lambda Values** - Agent-specific money preferences for realistic trading
- **Exchange Regimes** - Pure barter, pure monetary, or mixed economies
- **Money Scale** - Support for fractional prices (cents, dimes, etc.)

### **Visualization & Analysis**
- **Real-Time PyGame Display** - Watch agents move, trade, and forage
- **PyQt6 GUI** - Scenario browser, parameter editor, and log viewer
- **SQLite Telemetry** - Comprehensive logging with sub-second query times
- **Deterministic Reproducibility** - Same seed → identical results

---

## Project Structure

```
vmt-dev/
├── src/
│   ├── vmt_engine/          # Core 7-phase simulation engine
│   ├── vmt_launcher/        # PyQt6 GUI launcher application  
│   ├── vmt_pygame/          # PyGame visualization and rendering
│   ├── vmt_tools/           # Scenario builder and utilities
│   ├── telemetry/           # SQLite logging system
│   └── scenarios/           # Scenario schema and loading
├── scenarios/               # Pre-built YAML scenario files
│   └── demos/               # Tutorial and demo scenarios
├── tests/                   # 316+ comprehensive test suite
├── docs/                    # Full documentation
│   └── structures/          # Scenario parameter reference
├── launcher.py              # GUI entry point
└── main.py                  # CLI entry point
```

---

## Documentation

### **Getting Started**
- **[Project Overview](docs/1_project_overview.md)** - Complete feature overview and architecture
- **[Scenario Configuration Guide](docs/scenario_configuration_guide.md)** - Comprehensive parameter reference
- **[Scenario Parameter Reference](docs/structures/)** - Quick lookup tables and examples

### **Technical Documentation**
- **[Technical Manual](docs/2_technical_manual.md)** - Implementation details and algorithms
- **[Type Specifications](docs/4_typing_overview.md)** - Type system and invariants
- **[Strategic Roadmap](docs/3_strategic_roadmap.md)** - Development priorities and timeline

### **Quick Reference**
- **[Parameter Quick Reference](docs/structures/parameter_quick_reference.md)** - All parameters with ranges and typical values
- **[Comprehensive Template](docs/structures/comprehensive_scenario_template.yaml)** - Complete example with all parameters
- **[Minimal Example](docs/structures/minimal_working_example.yaml)** - Smallest working scenario
- **[Money Example](docs/structures/money_example.yaml)** - Monetary scenario with heterogeneous preferences

---

## Testing

Run the full test suite:

```bash
pytest
```

Run specific test categories:

```bash
# Money system integration tests
pytest tests/test_money_phase1_integration.py

# Pairing algorithm tests  
pytest tests/test_pairing_money_aware.py

# Mixed regime tests
pytest tests/test_mixed_regime_integration.py
```

---

## Development Status

### **Completed (P0 Resolved)**
- ✅ **Money-Aware Pairing** - Resolved pairing-trading mismatch (2025-10-22)
- ✅ **Core 7-Phase Engine** - Deterministic simulation loop
- ✅ **5 Utility Functions** - All utility types with full parameter support
- ✅ **Money System** - Quasilinear utility with heterogeneous λ values
- ✅ **SQLite Telemetry** - Comprehensive logging system
- ✅ **PyQt6 GUI** - Scenario browser and launcher
- ✅ **316+ Tests** - Comprehensive test coverage

### **Planned for Future Development**
- 🔄 **KKT Lambda Mode** - Endogenous λ estimation from market prices
- 🔄 **Mixed Liquidity Gated** - Barter fallback when money market thin
- 🔄 **Performance Benchmarks** - Large-scale scenario testing
- 🔄 **Distribution Syntax** - Random inventory generation

---

## Example Scenarios

### **Pedagogical Scenarios**
- **Foundational Barter** - Basic trading with CES preferences
- **Simple Money** - Introduction to monetary exchange
- **Heterogeneous Lambda** - Different money valuations across agents

### **Research Scenarios**
- **Large Scale** - 100+ agents for performance testing
- **Mixed Economy** - All trade types with mode scheduling
- **Subsistence Economy** - Stone-Geary preferences with survival constraints

### **Advanced Features**
- **Mode Scheduling** - Temporal control over agent behavior
- **Resource Claiming** - Realistic foraging with spatial competition
- **Heterogeneous Preferences** - Multiple utility types in single simulation

---

## License

See [LICENSE](LICENSE) file for details.

---

## Next Steps

1. **Try the demos** - Browse `scenarios/demos/` for tutorial scenarios
2. **Read the docs** - Start with [Project Overview](docs/1_project_overview.md)
3. **Create scenarios** - Use the GUI scenario builder or YAML templates
4. **Analyze results** - View telemetry with `python -m src.vmt_log_viewer.main`
5. **Run tests** - Verify everything works with `pytest`

**For contributors:** See [Strategic Roadmap](docs/3_strategic_roadmap.md) for development priorities and [Technical Manual](docs/2_technical_manual.md) for implementation details.