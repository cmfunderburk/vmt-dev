# VMT Strategic Roadmap

This document is the authoritative guide for the VMT project. It contains the high-level vision, long-term feature roadmap, and a detailed, actionable plan for the immediate next steps.

> **⚠️ Note on Phase Numbering**: This document uses "**Phases A-F**" for high-level curriculum progression. For detailed implementation plans, see:
> - **Money System**: [Money SSOT Plan](BIG/money_SSOT_implementation_plan.md) (Money Phases 1-6)
> - **Current Status**: [ADR-001](decisions/001-hybrid-money-modularization-sequencing.md) (strategic decision)
> - **Quick Lookup**: [Quick Reference Guide](quick_reference.md#by-phase-number-reconciliation)

---

## Part A: The Vision - A Microeconomic Laboratory

The VMT (Visualizing Microeconomic Theory) project is a **computational laboratory** for exploring economic principles. It is built on the paradigm of Agent-Based Computational Economics (ACE), a "bottom-up culture-dish approach" where complex, system-level patterns emerge from the localized interactions of autonomous agents.

The core philosophy is **"visualization-first."** Instead of static equations on a page, users get an interactive, simulation-driven environment to experiment with economic concepts. By manipulating parameters and observing agent behavior, users can see phenomena like market equilibrium and gains from trade emerge organically, fostering a deeper and more intuitive understanding.

The platform is designed to support two primary modes of use:
-   **Educational Mode**: Agents behave as the perfectly rational, utility-maximizing actors found in textbooks, allowing for the clear demonstration of canonical theories.
-   **Research Mode**: Rationality can be treated as a tunable parameter. Users can introduce bounded rationality, learning heuristics, or stochasticity to explore the boundaries of neoclassical models and ask novel research questions.

## Part B: Long-Term Roadmap

The long-term vision is to expand VMT step-by-step into a comprehensive microeconomic simulation platform that mirrors the progression of a standard graduate curriculum.

1.  **Phase A — Foraging & Barter Economy (Complete)**: The current state. A robust simulation of a two-good exchange economy with resource foraging and bilateral barter. This covers foundational concepts like utility maximization and gains from trade.

2.  **Phase B — Introduction of Money**: Transform the barter system by introducing a medium of exchange ("money") and explicit budget constraints. This enables the study of consumer choice and price systems.

3.  **Phase C — Local Market Mechanisms**: Graduate from bilateral negotiation to many-to-many trade. Implement posted-price markets or simple auctions where a market-clearing price can emerge from the collective behavior of a group of agents. This introduces supply and demand dynamics.

4.  **Production Economy**: Introduce "Firm" agents that use inputs (like labor, supplied by consumer agents) to produce goods according to production functions. This enables the study of producer theory, supply curves, and factor markets.

5.  **General Equilibrium & Welfare**: Simulate a multi-market economy where prices for goods and factors adjust to clear all markets simultaneously. This allows for the study of general equilibrium, welfare theorems, and market efficiency.

6.  **Advanced Topics**: Introduce modules for more advanced concepts, including:
    -   **Game Theory**: Explicitly model strategic interaction with matrix and repeated games.
    -   **Asymmetric Information**: Simulate markets with adverse selection ("lemons market") or moral hazard.
    -   **Mechanism Design**: Explore auctions, voting systems, and other designed mechanisms.

## Part C: Immediate Roadmap & Checklist (Phase A Polish → Phase C Market Prototype)

This section provides a concrete, step-by-step implementation plan for the next development cycle.

---

### **Milestone 1: Phase A Polish (The Foundation)**

**Goal**: Solidify the current Phase A barter engine. Ensure it is stable, well-documented, and provides a trusted foundation for all future features.

**Checklist:**
- [ ] **Core Engine Documentation:**
    - **Action:** Create `vmt_engine/README.md`.
    - **Details:** Write a technical overview of the 7-phase tick cycle and the responsibility of each system.
- [ ] **Code Clarity Pass:**
    - **Action:** Add explanatory comments to `matching.py`, `quotes.py`, and `utility.py`.
    - **Details:** Explain the "why" behind non-obvious logic (e.g., deterministic tie-breaking, the zero-inventory guard).
- [ ] **Foundational Scenario:**
    - **Action:** Create `scenarios/foundational_barter_demo.yaml`.
    - **Details:** Create a heavily-commented 3-4 agent scenario that serves as an executable tutorial.
- [ ] **Integration Test:**
    - **Action:** Create `tests/test_barter_integration.py`.
    - **Details:** Write a test that runs the foundational demo and asserts deterministic outcomes (final inventories, number of trades).

---

### **Milestone 2: Phase A→B Mode Toggles (The Easy Win)**

**Goal**: Create alternating "forage-only" and "trade-only" windows to create emergent budget constraints.

**Checklist:**
- [ ] **Modify Schema:**
    - **Action:** Add a `mode_schedule` dataclass to `scenarios/schema.py`.
    - **Details:** Should support `type: "global_cycle"`, `forage_ticks: int`, `trade_ticks: int`.
- [ ] **Modify Engine Loop:**
    - **Action:** In `vmt_engine/simulation.py`, determine `current_mode` based on the tick and schedule.
    - **Details:** Conditionally skip the `trade_phase()` or `forage_phase()` based on the current mode.
- [ ] **Modify Telemetry:**
    - **Action:** Add a `mode_changes` table to the database.
    - **Details:** Log `(tick, new_mode)` on every change. Add a `mode` column to the `decisions` log.

---

### **Milestone 3: Phase B — Introduce Money (The Core Refactor)**

**Goal**: Introduce money (M) as a tradable asset using the quasilinear utility model: `U_total = U_goods(A, B) + λ * M`. This requires refactoring the trade system to support generic good-to-good trades.

**Checklist:**
- [ ] **Update Core State (`state.py`):**
    - **Action:** Add `M: int = 0` to `Inventory`.
    - **Action:** Refactor `Quote` to hold quotes for all pairs (`A-B`, `A-M`, `B-M`).
- [ ] **Update Schema (`schema.py`):**
    - **Action:** Add `lambda_money: float` to `ScenarioParams`. Allow `M` in `initial_inventories`.
- [ ] **Refactor Utility Engine (`utility.py`):**
    - **Action:** Rename `u` to `u_goods`. Add a new `u_total(A, B, M)` method that includes the `λ * M` term.
    - **Action:** Add new `reservation_bounds` methods for money pairs (e.g., `reservation_bounds_A_in_M`).
- [ ] **Refactor Quote System (`quotes.py`):**
    - **Action:** Update `compute_quotes` to calculate and store quotes for all three trade pairs.
- [ ] **Refactor Matching System (`matching.py`):**
    - **Action:** Generalize `compute_surplus` to find the best surplus across all three pairs.
    - **Action:** Parameterize `find_compensating_block` and `execute_trade` to handle generic trades (e.g., `(good_to_buy, good_to_pay)`).
- [ ] **Update Tests:**
    - **Action:** Create `tests/test_money_quasilinear.py`.
    - **Action:** Update existing trade tests to use the new refactored, generic matching functions.

---

### **Milestone 4: Visualization Enhancements**

**Goal**: Improve visual clarity and user experience in Pygame renderer.

**Completed:**
- [x] **Smart Co-location Rendering** (2025-10-19):
    - Implemented geometric layouts for co-located agents (diagonal, triangle, corners, circle pack)
    - Added proportional sprite scaling based on agent count
    - Organized inventory label display for readability
    - Pure visualization enhancement - simulation state unchanged
    - 8 new tests in `tests/test_renderer_colocation.py`
    - Demo scenario: `scenarios/visual_clarity_demo.yaml`

**Future Enhancements:**
- [ ] **Hover Tooltips** (Roadmap):
    - **Action:** Add mouse hover detection to renderer
    - **Details:** When hovering over co-located agents, display popup with full agent details (IDs, inventories, utilities)
    - **Use Case:** Improves accessibility for cells with 4+ agents showing summary labels
- [ ] **Trade Indicators**:
    - **Action:** Draw animated lines between recently traded agents
    - **Details:** Visual feedback showing which agents just completed trades
- [ ] **Configurable Layouts**:
    - **Action:** Add UI toggle for classic vs smart co-location rendering
    - **Details:** Allow users to switch visualization styles in real-time

---

### **Milestone 5: Phase C — Prototype Posted-Price Market (The Payoff)**

**Goal**: Implement a "Local Posted-Price Auction" mechanism as the first true market in VMT.

**Checklist:**
- [ ] **Modify Simulation Loop (`simulation.py`):**
    - **Action:** In `trade_phase`, add logic to detect "connected components" (groups of agents within `interaction_radius` of each other).
- [ ] **Create Market Logic (`matching.py`):**
    - **Action:** Create a new `run_market(agent_ids)` function.
    - **Details:**
        - If `len(agent_ids) < market_min_size`, fall back to bilateral trade.
        - For a chosen market (e.g., "A" in terms of "M"), aggregate all bids and asks.
        - Determine a single clearing price `p_star` with a deterministic rule (e.g., midpoint of `max(bids)` and `min(asks)`).
        - Match willing buyers and sellers at `p_star`, sorting by `agent.id` for determinism.
        - Re-use the `find_compensating_block` logic with the fixed `p_star` to execute trades, still respecting `ΔU > 0` and one-trade-per-agent rules.
- [ ] **Update Telemetry:**
    - **Action:** Add a `market_events` table to the database.
    - **Details:** Log `(tick, market_id, clearing_price, volume)` for each market event.
