# VMT - Visualizing Microeconomic Theory

A spatial agent-based simulation platform for studying and comparing microeconomic exchange mechanisms. VMT moves beyond textbook assumptions by simulating how different institutional rules—from simple barter to monetary exchange—produce different market outcomes through discrete agent interactions.

## Overview

VMT is a research and teaching tool designed to make exchange mechanisms explicit and comparable. Instead of assuming an equilibrium, it models the *process* of exchange. Agents with heterogeneous preferences and utility functions operate in a spatial environment, foraging for resources and trading with one another based on a configurable set of rules (protocols).

The platform is architected to be a modular laboratory for comparative economics, enabling the study of:
- **Institutional Design**: What is the impact of different search, matching, and bargaining protocols on market outcomes?
- **Spatial Economics**: How do geography, search costs, and agent mobility influence economic activity?
- **Foundations of Exchange**: How do market-like outcomes emerge from purely bilateral interactions?

The project is under active development, with a focus on expanding the library of protocols and economic models available for comparative analysis.

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
Select a scenario from `scenarios/demos/` to run a simulation. The GUI provides the easiest way to explore VMT's features.

### Command Line
```bash
python main.py scenarios/demos/minimal_2agent.yaml
```

### View Results
```bash
python view_logs.py  # Open the interactive telemetry database viewer
```

## Project Structure

```
vmt-dev/
├── src/
│   ├── vmt_engine/         # Core simulation engine
│   │   ├── agent_based/    # Agent-based protocols (e.g., search)
│   │   ├── game_theory/    # Game theory protocols (e.g., matching, bargaining)
│   │   ├── systems/        # Phase-specific execution logic
│   │   ├── core/           # Agents, grid, core data structures
│   │   └── econ/           # Utility functions
│   ├── vmt_launcher/       # GUI Launcher for running scenarios
│   └── vmt_log_viewer/     # Interactive telemetry database viewer
├── scenarios/              # YAML configuration files for simulations
├── docs/                   # Documentation, plans, and specifications
├── tests/                  # Pytest suite (determinism is key!)
└── scripts/                # Analysis and utility scripts
```

## How It Works: The Simulation Tick

Each tick follows a deterministic 7-phase cycle:

1.  **Perception**: Agents observe the state of the world around them.
2.  **Decision**: Agents decide on their next action. This is a multi-step process orchestrated by protocols:
    -   *Search Protocol*: Agents identify potential trade partners or foraging targets.
    -   *Matching Protocol*: Agents form committed pairs for trading.
    -   Resource claims are made.
3.  **Movement**: Agents move towards their chosen targets.
4.  **Trade**: Paired agents execute the *Bargaining Protocol* to find and execute mutually beneficial trades.
5.  **Forage**: Unpaired agents at resource locations harvest them.
6.  **Resource Regeneration**: Resources on the grid regenerate based on scenario rules.
7.  **Housekeeping**: The system updates agent states, clears expired states (like trade cooldowns), and logs telemetry.

## Configuring Scenarios

Simulations are configured using YAML files. Key parameters include agent endowments, utility functions, and the active protocols.

```yaml
# Basic configuration
grid_size: 20
num_agents: 10
max_ticks: 1000

# Select protocols (institutional rules)
search_protocol: "myopic"
matching_protocol: "greedy_surplus"
bargaining_protocol: "compensating_block"

# Agent configuration
agents:
  - utility_function: "ces"
    params: {alpha_A: 0.5, alpha_B: 0.5, rho: 0.5}
    endowment: {A: 10, B: 10}
```

### Available Protocols

The protocol system is a key area of ongoing development. The following protocols are currently available.

**Search** (how agents find partners):
- `distance_discounted`: Chooses targets within vision radius by distance-discounted utility -- U(resource) vs U(trade-and-which-partner)
- `myopic`: A heuristic-based search where agents pursue the best nearby opportunity.
- `random_walk`: Agents explore the grid randomly. Useful for baseline comparisons.

**Matching** (how pairs form):
- `greedy_surplus`: Forms pairs based on the highest potential gains from trade.
- `random_matching`: Forms pairs randomly for baseline scenarios.

**Bargaining** (how prices are negotiated):
- `compensating_block`: A search for the first mutually beneficial integer-to-decimal block trade. This is the only fully implemented bargaining protocol and serves as the primary model for bilateral exchange.
- *Note*: Other bargaining protocols like `split_difference` and `take_it_or_leave_it` exist in the codebase as placeholders for future development but are not yet implemented.

## Development & Contribution

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest
```

Priority areas:
1.  **Protocol Implementation**: Flesh out planned bargaining protocols or add new search and matching mechanisms.
2.  **Scenario Development**: Create pedagogical examples that highlight specific economic phenomena.
3.  **Analysis Tools**: Build new scripts for visualization and statistical analysis.
4.  **Documentation**: Improve guides and examples.

The project's long-term vision and architectural plans are in `docs/planning_thinking_etc/BIGGEST_PICTURE/`.

## Roadmap & Future Work

VMT is an active research project. Key areas for future development include:

- **Theoretically Rigorous Monetary System**: Re-implementing a robust model of money is a top priority.
- **Expanding Bargaining Protocols**: Implementing `split_difference`, `take_it_or_leave_it`, and other classic bargaining models.
- **Centralized Markets**: Adding protocols for centralized exchange mechanisms like a Walrasian auctioneer or a double auction to allow for direct comparison with bilateral trade.
- **Intertemporal Choice**: Introducing models where agents can save and make decisions over multiple periods.
- **Advanced Agent Behavior**: Incorporating learning and strategic adaptation into agent decision-making.

## License

See [LICENSE](LICENSE) file for details.