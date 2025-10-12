# GitHub Copilot Instructions — VMT (Visualizing Microeconomic Theory)

Use these project-specific rules to implement a deterministic, utility-agnostic barter simulation. The planning specs are the source of truth: see `Planning-FINAL.md` and `algorithmic_planning.md`. Tests live in `tests/` and encode critical behaviors.

Core architecture and determinism
- Python 3.11; core deps: `numpy` (engine), `pygame` (GUI later). Keep runs deterministic.
- Iterate agents in ascending `agent.id`. Process trade pairs in ascending `(min_id, max_id)`.
- Tie-break partner choice by larger surplus, then lower id. Keep a fixed tick order: Perception → Decision → Movement → Trade → Forage → Housekeeping.

Utility families and reservation bounds
- Implement utilities in `econ/utility.py`: `UCES` (CES incl. Cobb–Douglas limit) and `ULinear`.
- Each utility exposes `reservation_bounds_A_in_B(A:int,B:int,eps)` returning `(p_min,p_max)`.
- Quotes are derived from bounds, not raw MRS: `ask = p_min*(1+spread)`, `bid = p_max*(1-spread)`. Refresh quotes after any inventory change (trade or forage).
- Zero-inventory guard (CES/CD): compute MRS/bounds using `(A+ε, B+ε)` internally; keep raw `(A,B)` for `u()` and ΔU checks. See `tests/test_reservation_zero_guard.py`.

Partner selection, matching, and trading
- Surplus overlap: for i vs j, consider `bid_i - ask_j` and `bid_j - ask_i`; pick positive max.
- Interaction: pairs within `interaction_radius` (0=same cell, 1=adjacent) are eligible; order pairs by `(min_id,max_id)`.
- Price rule: midpoint of crossed quotes in the chosen direction.
- Rounding and quantities: use round-half-up for B-per-A totals: `ΔB = floor(p*ΔA + 0.5)`; see `tests/test_trade_rounding_and_adjacency.py`. Do not use banker's rounding.
- Compensating multi-lot: scan ΔA from 1..ΔA_max; pick the first block with strict improvements for both agents: `u(A+ΔA,B-ΔB) > u(A,B)` for buyer and `u(A-ΔA,B+ΔB) > u(A,B)` for seller; ensure inventory feasibility. After each block, refresh quotes and repeat while surplus remains.

Conventions and parameters
- Defaults used in planning/tests: `spread=0.05`, `epsilon=1e-12`, `ΔA_max=5`, `vision_radius=3`, `interaction_radius=1`, `forage_rate=1`.
- Movement policy and GUI are secondary for v1; keep movement deterministic if implemented (consistent Manhattan tie-breaks).

Developer workflow anchors
- Tests: run `pytest` to validate engine behavior; current tests may skip until `econ/utility.py` exists. Key files: `tests/test_reservation_zero_guard.py`, `tests/test_trade_rounding_and_adjacency.py`.
- Scenarios YAML (if/when added) belong under `scenarios/` and should drive agents, grid, and params; follow the schemas outlined in the planning docs.

Do this, not that
- DO: derive quotes from reservation bounds; DON’T: quote raw MRS directly.
- DO: midpoint pricing + round-half-up; DON’T: banker’s rounding or float-to-int truncation.
- DO: preserve ordering/tie-break rules exactly; DON’T: use nondeterministic data structures or iteration order.