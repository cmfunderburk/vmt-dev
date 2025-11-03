# VMT - Visualizing Microeconomic Theory

[![Tests](https://img.shields.io/badge/tests-316%2B%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![Architecture](https://img.shields.io/badge/architecture-protocol--driven-orange)]()

A spatial agent-based simulation platform for studying microeconomic exchange mechanisms. Agents with heterogeneous preferences forage for resources and trade through configurable institutional rules (search, matching, and bargaining protocols).

## Overview

VMT is a research and teaching platform that makes exchange mechanisms explicit and comparable. Instead of assuming equilibrium prices, it simulates how different institutional rules produce different market outcomes through bilateral agent interactions.

**Core Features:**
- Spatial grid with resource foraging and agent movement
- Configurable protocols for search, matching, and bargaining
- Multiple utility functions (CES, Linear, Quadratic, Stone-Geary, Translog)
- Pure barter economy (A↔B trades only)
- Deterministic simulation (reproducible with seeds)
- Comprehensive telemetry and visualization

**Use Cases:**
- Teaching microeconomics through visualization
- Research on market mechanisms and institutional design
- Comparing bilateral vs centralized exchange systems

## Installation

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

## Quick Start

### GUI Interface
```bash
python launcher.py
```
Select a scenario from `scenarios/demos/` to see different exchange patterns.

### Command Line
```bash
python main.py scenarios/demos/demo_01_foundational_barter.yaml
```

### View Results
```bash
python view_logs.py  # Open telemetry database viewer
```

## Project Structure

```
vmt-dev/
├── src/vmt_engine/       # Core simulation engine
│   ├── protocols/        # Swappable institutional rules
│   ├── systems/          # Phase-specific execution
│   ├── core/             # Agents, grid, state
│   └── econ/             # Utility functions
├── scenarios/            # YAML configuration files
│   └── demos/            # Example scenarios
├── docs/                 # Documentation
│   └── BIGGEST_PICTURE/  # Vision and architecture
├── tests/                # Test suite
└── scripts/              # Analysis tools
```

## Configuring Simulations

### Scenario Files (YAML)

Scenarios define agent preferences, spatial layout, and institutional rules:

```yaml
# Basic configuration
grid_size: 10
num_agents: 20
max_ticks: 100

# Select protocols (institutional rules)
search_protocol: "legacy_distance_discounted"     # or "random_walk"
matching_protocol: "legacy_three_pass"            # or "random_matching"
bargaining_protocol: "compensating_block"  # or "split_difference"

# Agent configuration
agents:
  - utility_function: "ces"
    params: {alpha_A: 0.5, alpha_B: 0.5, rho: 0.5}
    endowment: {A: 10, B: 10}
```

See `docs/structures/` for complete templates and `scenarios/demos/` for examples.

### Available Protocols

**Search** (how agents find partners):
- `legacy_distance_discounted`: Utility-weighted by distance
- `random_walk`: Random movement

**Matching** (how pairs form):
- `legacy_three_pass`: Mutual consent with fallback
- `random_matching`: Random pairing

**Bargaining** (how prices are negotiated):
- `compensating_block`: Bilateral feasibility search
- `split_difference`: Equal surplus division

Query available protocols programmatically:
```python
from src.vmt_engine.protocols import list_all_protocols
list_all_protocols()
# Returns dict of available protocols by category
```

## Simulation Phases

Each tick follows a deterministic 7-phase cycle:

1. **Perception**: Agents observe local state
2. **Movement**: Agents move toward targets
3. **Foraging**: Resource collection from grid
4. **Trading**: Bilateral exchange through protocols
5. **Consumption**: Utility calculation
6. **Regeneration**: Resources respawn
7. **Housekeeping**: State updates and logging

## Documentation

**Getting Started:**
- [Project Overview](docs/1_project_overview.md) - Detailed feature documentation
- [Scenario Configuration](docs/structures/) - How to create scenarios
- [Tutorial Scenarios](scenarios/demos/) - Example configurations

**Architecture:**
- [Vision and Architecture](docs/BIGGEST_PICTURE/vision_and_architecture.md) - Research goals and design philosophy
- [Technical Manual](docs/2_technical_manual.md) - Implementation details
- [Protocol Development](docs/protocols_10-27/) - Adding new mechanisms

**Development:**
- [Developer Onboarding](docs/onboarding/README.md) - Setup and architecture guide
- [Type Specifications](docs/4_typing_overview.md) - Type system documentation
- [Enhancement Backlog](docs/3_enhancement_backlog.md) - Planned features

## Testing

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS

# Run all tests
pytest

# Run specific test categories
pytest tests/test_foundational_baseline_trades.py
pytest tests/test_protocol_registry.py
```

## Research Applications

VMT enables comparative analysis of exchange mechanisms:

1. **Price Formation**: When do bilateral negotiations converge to uniform prices?
2. **Institutional Comparison**: How do different protocols affect efficiency and distribution?
3. **Spatial Effects**: Role of geography and search costs in market outcomes
4. **Information Frictions**: Impact of limited visibility and memory

Future extensions include centralized market mechanisms (Walrasian auctioneer, posted prices, double auctions) to enable direct comparison with bilateral exchange.

## Contributing

Priority areas for contribution:

1. **Protocol Implementation**: Add new search, matching, or bargaining mechanisms
2. **Scenario Development**: Create pedagogical examples
3. **Analysis Tools**: Build visualization and statistical analysis scripts
4. **Documentation**: Improve guides and examples

See [Enhancement Backlog](docs/3_enhancement_backlog.md) for specific tasks.

## License

See [LICENSE](LICENSE) file for details.

## Next Steps

1. Run a demo: `python launcher.py`
2. Explore scenarios in `scenarios/demos/`
3. Read [Vision and Architecture](docs/BIGGEST_PICTURE/vision_and_architecture.md) for research context
4. Create custom scenarios using templates in `docs/structures/`
5. Analyze results with `python view_logs.py`