# VMT v1 - Virtual Market Testbed

A discrete-time agent-based simulation for studying emergent market dynamics with foraging, trade, and heterogeneous utility functions.

## Overview

VMT v1 implements a minimal but complete market simulation with:
- **Foraging**: Agents harvest resources (A and B) from a grid
- **Trade**: Bilateral quote-based trading with midpoint pricing
- **Heterogeneous utilities**: CES and Linear utility functions
- **Deterministic execution**: Reproducible via RNG seeding
- **Telemetry**: Comprehensive logging for analysis

## Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
PYTHONPATH=. pytest tests/ -v

# Run simulation with visualization (requires pygame)
python main.py scenarios/three_agent_barter.yaml
```

## Project Structure

```
vmt-dev/
├── vmt_engine/          # Core simulation engine
│   ├── core/            # Grid, agents, state structures
│   ├── econ/            # Utility functions
│   ├── systems/         # Perception, movement, matching, foraging
│   └── simulation.py    # Main simulation loop
├── vmt_pygame/          # Pygame visualization
├── scenarios/           # YAML scenario definitions
├── telemetry/           # Logging and snapshots
└── tests/               # Test suite
```

## Usage

### Running a Scenario

```python
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario

scenario = load_scenario("scenarios/single_agent_forage.yaml")
sim = Simulation(scenario, seed=42)
sim.run(max_ticks=100)
```

### Creating Custom Scenarios

See `scenarios/single_agent_forage.yaml` and `scenarios/three_agent_barter.yaml` for examples.

## Development

This implementation follows the structured plan in `vmt-v1--implementation-plan.plan.md`, organized into milestones:

- **M0**: Core loop skeleton and telemetry hooks
- **M1**: Foraging system (movement, perception, harvesting)
- **M2**: Quote generation and partner targeting
- **M3**: Trade matching and execution
- **M4**: Comprehensive testing and validation
- **M5**: Pygame visualization

## License

See LICENSE file for details.

