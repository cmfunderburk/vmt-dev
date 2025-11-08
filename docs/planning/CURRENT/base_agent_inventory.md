# BaseAgent vs SpatialAgent Inventory

## Purpose
Summarize the current responsibilities of `src/vmt_engine/core/agent.py` and identify how they split between a proposed `BaseAgent` and `SpatialAgent`.

## Current Agent Responsibilities (Status Quo)
- **Identity & Utility**: `id`, optional `utility` pointer, and `inventory` of goods A/B represented by `Inventory` dataclass.
- **Pricing Interface**: `quotes` dictionary for barter terms and reservation prices.
- **Spatial State**: `pos`, `home_pos`, `target_pos`, and `forage_target_pos` for the grid-based movement system.
- **Mobility Parameters**: `vision_radius`, `move_budget_per_tick` governing perception and movement limits.
- **Matching/Decision Cache**: `_preference_list`, `_decision_target_type`, `target_agent_id` for search and matching phases.
- **Runtime Flags**: `inventory_changed`, `is_foraging_committed`, `paired_with_id`, `trade_cooldowns`, `perception_cache` used to coordinate tick-to-tick actions.

## Candidate `BaseAgent` Scope
- **Core Identity**: `id` (non-negative constraint) and optional `utility` object reference.
- **Endowments & Consumption**: `inventory` with helper methods for deterministic updates (reuse existing validations in `Inventory`).
- **Economic Interface**: accessors for quotes or reservation prices only if Game Theory modules require them; otherwise keep quotes in subclasses and offer neutral hooks (`get_reservation_price()` etc.).
- **Utility Evaluation Hooks**: thin wrappers for `utility.compute` and demand/optimization helpers planned for Game Theory (`compute_mrs`, `optimal_bundle` once implemented).
- **Deterministic RNG Handle (if needed)**: shared reference to simulation RNG or a pure function interface for reproducible calculations.

## Candidate `SpatialAgent` Additions
- **Spatial Coordinates**: `pos`, `home_pos`, `target_pos`, `forage_target_pos`.
- **Movement Parameters**: `vision_radius`, `move_budget_per_tick` and any pathing helpers.
- **Search/Matching State**: `_preference_list`, `_decision_target_type`, `target_agent_id`, `paired_with_id`.
- **Foraging & Resource Coordination**: `is_foraging_committed`, `trade_cooldowns`, `perception_cache`.
- **Quotes Management**: retain barter `quotes` here if they are specific to spatial protocols; expose a clean API to BaseAgent for price expectations if shared.

## Additional Artifacts to Review
- **Telemetry**: confirm which agent fields are logged in `logs/telemetry.db` and adjust serialization boundaries accordingly.
- **WorldView Contracts**: audit how search/matching code accesses agent attributes; catalogue any direct field expectations before refactor.
- **Tests**: inventory determinism and protocol tests touching agent internals to prepare refactor-safe shims.
- **Scenario Loading**: ensure scenario YAML parsing still constructs correct subclass type once split occurs.
