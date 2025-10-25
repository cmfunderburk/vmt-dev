# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-316%2B%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green)]()

A spatial agent-based simulation for teaching and researching microeconomic behavior. Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral trade (barter or monetary exchange) using reservation-price negotiation.

**Key Features:** 7-phase deterministic engine • 5 utility functions (CES, Linear, Quadratic, Translog, Stone-Geary) • Money-aware trading • Real-time visualization • Comprehensive telemetry

---

## Quick Start

### Installation

```bash
# Clone repository and navigate to it
cd vmt-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run Your First Simulation

**GUI (Recommended):**
```bash
python launcher.py
```
Select `scenarios/demos/demo_01_foundational_barter.yaml` and click "Launch Simulation"

**Command Line:**
```bash
python main.py scenarios/demos/demo_01_foundational_barter.yaml
```

---

## What VMT Does

VMT is an agent-based model for studying microeconomic exchange mechanisms through visualization:

- **Spatial Foraging:** Agents move on an N×N grid collecting resources A and B
- **Bilateral Trading:** Agents pair up and negotiate trades based on reservation prices derived from marginal utilities
- **Money System:** Supports pure barter, pure monetary, and mixed exchange regimes with quasilinear utility
- **Deterministic:** Same seed always produces identical results for reproducibility
- **Comprehensive Telemetry:** SQLite logging captures all trades, movements, and state changes

**Built For:**
- Economics pedagogy (visualize trading behavior in real-time)
- Research (test mechanism design hypotheses)
- Experimentation (compare barter vs monetary exchange, heterogeneous preferences, etc.)

---

## Current Status

**Production Ready:**
- ✅ 7-phase simulation engine (perception → decision → movement → trade → forage → regeneration → housekeeping)
- ✅ 5 utility functions with full parameter support
- ✅ Money-aware pairing algorithm (P0 resolved Oct 2025)
- ✅ PyQt6 GUI launcher and log viewer
- ✅ SQLite telemetry system
- ✅ 316+ tests with deterministic validation

**Planned:**
- 🔄 Protocol modularization (swappable bargaining/matching mechanisms)
- 🔄 KKT lambda mode (endogenous money demand estimation)
- 🔄 Advanced market mechanisms (posted prices, auctions)

See [docs/3_strategic_roadmap.md](docs/3_strategic_roadmap.md) for detailed development timeline.

---

## Project Structure

```
vmt-dev/
├── src/
│   ├── vmt_engine/       # Core simulation engine
│   ├── vmt_launcher/     # PyQt6 GUI
│   ├── vmt_pygame/       # Visualization renderer
│   └── telemetry/        # SQLite logging
├── scenarios/            # YAML scenario files
│   └── demos/            # Tutorial scenarios
├── tests/                # 316+ test suite
├── docs/                 # Full documentation
├── launcher.py           # GUI entry point
└── main.py               # CLI entry point
```

---

## Documentation

**Getting Started:**
- [Project Overview](docs/1_project_overview.md) - Complete feature walkthrough
- [Scenario Configuration Guide](docs/scenario_configuration_guide.md) - How to create scenarios
- [Parameter Reference](docs/structures/parameter_quick_reference.md) - All parameters and typical values

**For Developers:**
- [Technical Manual](docs/2_technical_manual.md) - Implementation details and algorithms
- [Strategic Roadmap](docs/3_strategic_roadmap.md) - Development priorities
- [Type Specifications](docs/4_typing_overview.md) - Type system and invariants

**Quick Reference:**
- [Comprehensive Template](docs/structures/comprehensive_scenario_template.yaml) - Example with all features
- [Minimal Template](docs/structures/minimal_working_example.yaml) - Simplest working scenario
- [Money Template](docs/structures/money_example.yaml) - Monetary exchange example

---

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_money_phase1_integration.py      # Money system
pytest tests/test_pairing_money_aware.py           # Pairing algorithm
pytest tests/test_mixed_regime_integration.py      # Mixed regimes
```

---

## Usage Examples

### Pedagogical Use
Use the GUI to demonstrate:
- How reservation prices emerge from marginal utilities
- Gains from trade in barter vs monetary economies
- Effects of heterogeneous preferences on trade patterns

### Research Use
Create custom scenarios to study:
- Mechanism design (compare matching algorithms)
- Money vs barter efficiency
- Effects of spatial distribution on trade emergence
- Role of search costs in exchange

### Development
- **Add utility functions:** Implement `UtilityBase` ABC in `src/vmt_engine/econ/utility.py`
- **Create scenarios:** Use GUI builder or edit YAML files in `scenarios/`
- **Analyze data:** Query SQLite database with custom scripts or log viewer

---

## License

See [LICENSE](LICENSE) file for details.

---

## Next Steps

1. **Run a demo:** `python launcher.py` → select demo scenario → launch
2. **Read the overview:** [docs/1_project_overview.md](docs/1_project_overview.md)
3. **Create a scenario:** Use GUI scenario builder or copy a template from `docs/structures/`
4. **Analyze results:** `python -m src.vmt_log_viewer.main` to explore telemetry
5. **Contribute:** See [docs/3_strategic_roadmap.md](docs/3_strategic_roadmap.md) for development priorities

**Questions or issues?** Check the [Technical Manual](docs/2_technical_manual.md) or review test files in `tests/` for usage examples.
