# Changelog

All notable changes to the VMT (Visualizing Microeconomic Theory) simulation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- **Bargaining Protocol Architecture Correction** (2025-11-04): Removed incorrect abstraction
  - Deleted `TradeDiscoverer` interface (protocols should be self-contained)
  - Inlined search logic into `CompensatingBlockBargaining` protocol
  - Converted `SplitDifference` and `TakeItOrLeaveIt` to honest stubs (not_implemented)
  - Added `trade_tuple_to_effect()` shared utility for TradeTuple conversion
  - Clarified architectural principle: protocols define mechanisms, not just allocation rules

- **Matching-Bargaining Decoupling Refactor** (2025-11-03): Separated matching from bargaining concerns
  - Decoupled matching protocols from bargaining implementations via abstraction interfaces
  - `BargainingProtocol.negotiate()` now receives agents directly (breaking change)
  - `ProtocolContext` now includes agents dict for matching protocols (breaking change)
  - Eliminated ALL params hacks (both bargaining and matching)
  - Renamed `legacy_compensating_block` protocol to `compensating_block` (reflects actual purpose)
  - Matching protocols now use lightweight heuristics; bargaining protocols use full discovery
  - Benefits: Independent protocol development, cleaner architecture, correct semantic separation

### Added
- `TradePotentialEvaluator` interface for lightweight matching phase evaluation
- `QuoteBasedTradeEvaluator`: Default evaluator using quote overlaps (fast heuristic)
- `TradePotential` and `TradeTuple` NamedTuples for zero-overhead data passing
- `trade_tuple_to_effect()` utility function for converting TradeTuple to Trade effect
- Debug immutability assertions in `TradeSystem` (activated via `debug_immutability` param)
- Comprehensive test suite for trade evaluation abstractions

### Removed
- `build_trade_world_view()` function (params hack eliminated)
- `legacy.py` bargaining protocol (replaced by `compensating_block.py`)
- `find_compensating_block_generic()` from `matching.py` (moved to `CompensatingBlockDiscoverer`)
- `find_all_feasible_trades()` from `matching.py` (no longer needed)
- `find_best_trade()` from `matching.py` (no longer needed)
- All `_build_agent_from_world()` adapter methods from bargaining protocols
- All `_build_agent_from_context()` adapter methods from matching protocols
- `TradeDiscoverer` ABC and `CompensatingBlockDiscoverer` as separate class
- `discovery.py` module
- Incomplete implementations masquerading as working protocols (split_difference, take_it_or_leave_it)

- **Protocol Architecture Restructure** (2025-11-02): Moved protocols to domain-specific modules
  - Search protocols moved from `vmt_engine.protocols.search` to `vmt_engine.agent_based.search`
  - Matching protocols moved from `vmt_engine.protocols.matching` to `vmt_engine.game_theory.matching`
  - Bargaining protocols moved from `vmt_engine.protocols.bargaining` to `vmt_engine.game_theory.bargaining`
  - Effect types remain in `vmt_engine.protocols.base` (unchanged)
  - Registry system remains in `vmt_engine.protocols.registry` (unchanged)
  - YAML scenario files work identically (backward compatible via registry)
  - Import paths now reflect theoretical paradigms (Agent-Based vs Game Theory)
  - Benefits: clearer architecture, better extensibility for future domain-specific modules

- **GUI Framework Migration** (2025-10-22): Migrated from PyQt5 to PyQt6
  - Updated all imports from `PyQt5` to `PyQt6`
  - Updated Qt enum references to use proper namespaces (e.g., `Qt.UserRole` → `Qt.ItemDataRole.UserRole`)
  - Replaced deprecated `exec_()` with `exec()`
  - Updated documentation and requirements.txt