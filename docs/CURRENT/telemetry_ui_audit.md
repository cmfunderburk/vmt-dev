# Telemetry & UI Dependency Audit

## Scope
Inventory dependencies on the current `Agent` structure within:
- `src/telemetry/` (logging, schema, data writers)
- `src/vmt_log_viewer/` (Qt-based telemetry viewer)

Goal: identify which agent fields are assumed to exist so that `BaseAgent`/`SpatialAgent` refactor can preserve logging fidelity.

## Telemetry (Database Logging)
- **`TelemetryManager.log_agent_snapshots`**
  - Requires: `agent.id`, `agent.pos`, `agent.inventory.A/B`, `agent.utility`, `agent.quotes`, `agent.target_agent_id`, `agent.target_pos`, `agent.inventory_changed` (indirect via quote refresh elsewhere).
  - Stores positions as integers and inventories via `to_storage_int` → schema requires spatial coordinates.
- **`TelemetryManager.log_decision`**
  - Expects: `agent.target_pos`, `agent.target_agent_id`, `agent.paired_with_id`, `agent.is_foraging_committed` for logging flags.
- **`TelemetryManager.log_trades` / `log_trade_attempt`**
  - Uses `buyer/seller.id`, inventories, utility evaluations, quotes; assumes spatial positions provided by caller (TradeSystem uses `pos`).
- **Buffer flush methods / schema (`telemetry/database.py`)**
  - Tables `agent_snapshots`, `decisions`, `trades`, `trade_attempts`, `pairings`, `preferences` all include positional fields or target references.
  - Any schema change would require migration + viewer updates; better to keep spatial data in `SpatialAgent` and ensure telemetry continues to receive that subclass.
- **Imports**: Telemetry modules import `Agent` behind `TYPE_CHECKING`; runtime expects objects with current attributes.

## UI (Log Viewer)
- **`AgentViewWidget`**
  - Displays: position `(x, y)`, inventory, utility, quotes, target agent/position.
  - Assumes telemetry table includes these fields; order tied to schema.
- **`TradeViewWidget` / `Timeline` / `Overview`** (inspected via `viewer.py` and `queries.py`)
  - Rely on trades table containing buyer/seller IDs and coordinate data for plotting.
- **QueryBuilder**
  - Hardcodes column names from telemetry schema; expects `agent_snapshots` to include positional columns, `decisions` to include targets, etc.
- **Renderer (`vmt_pygame/renderer.py`)**
  - Uses live `Simulation` agents, not telemetry, but still depends on `agent.pos`, `quotes`, etc.; will need `SpatialAgent`.

## Implications for BaseAgent Split
- Telemetry logging must continue receiving agents with spatial attributes; we can supply `SpatialAgent` instances unchanged.
- Game Theory modules consuming `BaseAgent` should bypass telemetry schema that assumes spatial context, implying optional logging path (e.g., simplified telemetry or none).
- If future tracks need telemetry without spatial data, consider separate logging schema; for now, maintain existing tables for spatial simulations.
- During refactor, ensure `TelemetryManager` type hints updated to accept `SpatialAgent` while keeping interfaces stable.

## Recommended Actions
1. **Explicit Contract**: Document that `TelemetryManager` expects `SpatialAgent` instances; update docstrings after refactor.
2. **Schema Compatibility**: Avoid altering existing SQLite schema; update migration plan accordingly.
3. **Game Theory Logging Plan**: Decide whether Game Theory track writes to telemetry (if yes, need alternative schema or adapter that fills spatial fields with defaults).
4. **UI Documentation**: Note that log viewer interprets current schema; any BaseAgent-only runs would need either spatial enrichment or viewer adjustments.
