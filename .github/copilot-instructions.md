# GitHub Copilot Instructions for the VMT Codebase

This document provides essential guidance for AI agents working on the Visualizing Microeconomic Theory (VMT) project. The project is a Python-based microeconomic simulation.

Refer to `Planning-FINAL.md` for the high-level architecture and `algorithmic_planning.md` for the detailed, source-of-truth agent behavior.

## 1. Core Architecture & Principles

- **Language:** Python 3.11 with `pygame` for visualization and `numpy`.
- **Determinism is Critical:** The simulation must be fully deterministic.
    - Agent processing loops must iterate in ascending `agent.id`.
    - Trade-matching loops must process pairs in ascending `(min_id, max_id)`.
    - Tie-breaking rules (e.g., for partner selection) are specified in the planning documents and must be followed precisely.
- **Utility-Agnostic Engine:** The core trading logic in the simulation engine is designed to be independent of specific utility functions. It interacts with utility models through a shared interface defined in the `econ` module.
- **Tick Order:** The simulation proceeds in discrete, ordered ticks:
    1.  Perception
    2.  Decision
    3.  Movement
    4.  Trade
    5.  Forage
    6.  Housekeeping (e.g., quote refreshes, logging)

## 2. Key Economic Logic & Algorithms

The agent interaction logic is highly specific. Do not use generic trading algorithms.

- **Utility Module (`econ/utility.py`):** This is the heart of the economic logic. For v1, it should contain implementations for `UCES` (Constant Elasticity of Substitution) and `ULinear` utility functions.
    - Each utility class must implement the `reservation_bounds_A_in_B(A, B, eps)` method, which is the primary interface for the trade engine.
- **Quote Generation:** Agent quotes are **not** directly their Marginal Rate of Substitution (MRS). They are derived from reservation price bounds:
    - `p_min, p_max = agent.utility.reservation_bounds_A_in_B(...)`
    - `ask_A_in_B = p_min * (1 + spread)`
    - `bid_A_in_B = p_max * (1 - spread)`
    - Quotes must be refreshed any time an agent's inventory changes (from trading or foraging).
- **Partner Selection:** Agents find partners by identifying the largest positive "surplus overlap" between their bid/ask quotes and those of their neighbors.
- **Trade Execution:**
    - **Price:** The trade price is the **midpoint** of the seller's ask and the buyer's bid.
    - **Compensating Multi-Lot Rounding:** This is a critical, non-obvious algorithm. Given a price, the engine must search for the smallest integer quantity `ΔA >= 1` such that the corresponding `ΔB = round(p * ΔA)` results in a strict utility improvement (`ΔU > 0`) for **both** the buyer and seller. See `algorithmic_planning.md` for the exact procedure.
- **Zero-Inventory Guard:** For CES utility, when an agent has zero inventory (`A=0, B=0`), the reservation bounds calculation must use `(A+epsilon, B+epsilon)` to avoid division by zero, but only for the internal MRS calculation. The agent's actual inventory and `u()` calculations remain `(0,0)`.

## 3. Development & Testing

- **Testing Framework:** `pytest` is used for testing. See the `tests/` directory for examples.
- **Test Focus:** Tests should cover economic edge cases, deterministic behavior, and adherence to the specified algorithms. `test_reservation_zero_guard.py` is a good example of a targeted test for a specific rule.
- **Scenarios:** Simulation runs are configured via YAML files in the `scenarios/` directory. These files define grid size, agent populations, utility functions, and economic parameters.

When implementing new features, always refer back to the planning documents to ensure your implementation matches the specified logic and maintains determinism.