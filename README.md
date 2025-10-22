# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-316%2B%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green)]()

A spatial agent-based simulation for teaching and researching microeconomic behavior through visualization.

Agents with heterogeneous preferences forage for resources on a grid and engage in bilateral trade (barter or monetary exchange) using reservation-price-based negotiation.

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

## Project Structure

```
vmt-dev/
├── src/
│   ├── vmt_engine/      # Core simulation engine
│   ├── vmt_launcher/    # GUI launcher application
│   ├── vmt_pygame/      # Pygame visualization
│   └── scenarios/       # Scenario loading and schema
├── scenarios/           # Pre-built scenario configurations
│   └── demos/          # Tutorial scenarios
├── tests/              # 316+ comprehensive tests
├── docs/               # Full documentation
├── launcher.py         # GUI entry point
└── main.py            # CLI entry point
```

---

## Documentation

- **[Project Overview](docs/1_project_overview.md)** - Features, architecture, and detailed usage
- **[Technical Manual](docs/2_technical_manual.md)** - Implementation details and algorithms
- **[Scenario Configuration Guide](docs/scenario_configuration_guide.md)** - How to create scenarios
- **[Type Specifications](docs/4_typing_overview.md)** - Type system and invariants

---

## Key Features

- **Spatial Foraging** - Agents move on a grid collecting resources
- **Bilateral Trading** - Barter and monetary exchange modes
- **Rich Utility Functions** - Linear, quadratic, CES, Stone-Geary, translog
- **Money-Aware Pairing** - Smart matching for trading agents
- **Real-Time Visualization** - PyGame display with agent states
- **Comprehensive Telemetry** - SQLite database logging for analysis
- **Deterministic** - Reproducible simulations with seed control

---

## Testing

Run the full test suite:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/test_money_phase1_integration.py
```

---

## License

See [LICENSE](LICENSE) file for details.

---

## Next Steps

- Browse demo scenarios in `scenarios/demos/` 
- Read the [Project Overview](docs/1_project_overview.md) for comprehensive documentation
- Examine telemetry data with `python view_logs.py`
- Create custom scenarios using the GUI scenario builder

