# VMT Project Vision & Roadmap

**Status**: Stages 0-2 Complete. Actively working on Stage 3.

---

## 1. Executive Summary & Core Vision

VMT (Visualizing Microeconomic Theory) is evolving from a spatial agent-based simulation into a comprehensive pedagogical and research platform with three complementary paradigms:
1.  **Agent-Based Track**: Emergent market phenomena from spatial bilateral trading.
2.  **Game Theory Track**: Strategic interactions with Edgeworth Box visualizations.
3.  **Neoclassical Track**: Equilibrium benchmarks using traditional solution methods.

The pedagogical innovation is to allow students to build markets from individual agent interactions and compare emergent outcomes with theoretical predictions, demonstrating why institutional details matter.

The fundamental premise is that markets are **institutional constructions**, not natural phenomena. VMT demonstrates how market-like behavior emerges (or fails to emerge) from micro-level interactions and institutional rules.

---

## 2. Core Architecture

### Key Principles:
- **Three-Track Paradigm**: Agent-Based, Game Theory, Neoclassical.
- **Shared Core**: All tracks share economic primitives (Agent, Utility, Trade).
- **Protocol Ownership**:
    - **`game_theory/` owns**: Bargaining and Matching protocols.
    - **`agent_based/` owns**: Search protocols (which are inherently spatial).
    - The Agent-Based track imports and uses protocols from the Game Theory track for consistency.

---

## 3. Implementation Roadmap

| Stage                                       | Status      | Detailed Plan                                        |
| ------------------------------------------- | ----------- | ---------------------------------------------------- |
| **0. Protocol Restructure**                 | ✅ Complete | (see `archive/`)                                     |
| **1. Foundational Analysis**                | ✅ Complete | (see `archive/`)                                     |
| **2. Protocol Diversification**             | ✅ Complete | (see `archive/`)                                     |
| **3. Game Theory Track**                    | 🔵 **Next Up** | [1_Implementation_Stage3_GameTheory.md](./1_Implementation_Stage3_GameTheory.md) |
| **4. Unified Launcher**                     | ⚪️ Planned  | [2_Implementation_Stage4_Launcher.md](./2_Implementation_Stage4_Launcher.md) |
| **5. Market Information Systems**           | ⚪️ Planned  | [3_Implementation_Stage5_MarketInfo.md](./3_Implementation_Stage5_MarketInfo.md) |
| **6. Neoclassical Benchmarks**              | ⚪️ Planned  | [4_Implementation_Stage6_Neoclassical.md](./4_Implementation_Stage6_Neoclassical.md) |
