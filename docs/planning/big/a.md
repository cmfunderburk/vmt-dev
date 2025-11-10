# BIG Refactor Plan to De-LLM the Project

Functionally, the current project provides a sound baseline. Structurally, it needs a lot of work for extensibility and maintainability.

As it stands, the vmt-engine/ directory is fragmented beyond what either economic theory or code clarity would suggest. 

The folder structure:
```
vmt-engine/
├── agent_based/
├── core/
├── econ/
├── game_theory/
├── protocols/
├── systems/
├── simulation.py
├── __init__.py
```

This is extremely unwieldy.

To fix this, we need to think hard about the logical coherence of the project.

The main entry point, for the user, is through the launcher. In the launcher, they will be presented with a menu to choose
whether to enter the agent-based engine, the game theory engine, or the neoclassical engine.

For the developer/maintainer: the vmt-engine/ structure needs to be in accordance with economic and code clarity logic.

For example,

vmt-engine/
├── spatial/ # will contain code strictly dedicated to the spatial model, e.g. grid.
├── agent/ # will contain BaseAgent and other necessary agent-centric code. A utility_fn/ subdirectory will contain all utility functions.
├── game_theory/ # will contain code related to running the protocols through the game theory GUI (not yet created); all protocols will live here in subdirectories for search, matching, and bargaining.
├── simulation.py
├── __init__.py
```