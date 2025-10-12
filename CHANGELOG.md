# Changelog

All notable changes to the VMT (Visualizing Microeconomic Theory) simulation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Fixed
- Nothing yet

---

## [1.1.0] - 2025-10-12

### Added - Logging System Overhaul

#### SQLite Database Backend
- **New telemetry system** with SQLite database storage replacing CSV files
- **99.1% space reduction** for standard logging (644 MB → 5.88 MB)
- **Three configurable log levels**: SUMMARY, STANDARD, DEBUG
- **Multiple runs** tracked in single database file
- **Fast queries**: Sub-second data retrieval with proper indexing
- **Batch writing**: Configurable batch size (default 100) for performance

#### Interactive Log Viewer
- **New PyQt5 log viewer application** (`vmt_log_viewer/`)
- **Timeline scrubber**: Navigate through simulation ticks
- **Agent analysis**: State tracking, trajectories, trade history
- **Trade visualization**: Details, attempts, statistics
- **Decision exploration**: Partner selection, movement tracking
- **Resource viewer**: Distribution over time
- **CSV export**: Backward compatibility when needed

#### Files Added
- `telemetry/database.py` - SQLite connection & schema
- `telemetry/config.py` - LogConfig & LogLevel classes
- `telemetry/db_loggers.py` - TelemetryManager (main logger)
- `vmt_log_viewer/viewer.py` - Main PyQt5 window
- `vmt_log_viewer/queries.py` - SQL query helpers
- `vmt_log_viewer/csv_export.py` - Database → CSV export
- `vmt_log_viewer/widgets/timeline.py` - Timeline scrubber widget
- `vmt_log_viewer/widgets/agent_view.py` - Agent analysis widget
- `vmt_log_viewer/widgets/trade_view.py` - Trade visualization widget
- `vmt_log_viewer/widgets/filters.py` - Query filter widget
- `view_logs.py` - Launch log viewer
- `example_new_logging.py` - Usage examples

### Added - GUI Launcher System

#### Main Components
- **GUI launcher window** (`vmt_launcher/launcher.py`) for browsing and running scenarios
- **Scenario builder** (`vmt_launcher/scenario_builder.py`) with 4-tab interface
- **Input validator** (`vmt_launcher/validator.py`) with comprehensive error checking
- **Built-in documentation panel** in Utility Functions tab with rich HTML formatting
- **Auto-refresh**: Detects new scenarios automatically
- **Subprocess launching**: Keeps GUI responsive during simulations

#### Scenario Builder Features
- **Tab 1: Basic Settings** - Name, grid, agents, inventories
- **Tab 2: Simulation Parameters** - Spread, vision, movement, trade cooldown
- **Tab 3: Resources** - Density, growth, regeneration cooldown
- **Tab 4: Utility Functions** - CES and Linear with in-context documentation
- **Dynamic utility rows**: Add/remove utility types
- **Auto-normalize weights**: Ensures weights sum to 1.0
- **YAML generation**: Valid schema-compliant output

#### Files Added
- `vmt_launcher/launcher.py` - Main launcher window (211 lines)
- `vmt_launcher/scenario_builder.py` - Scenario builder dialog (669 lines)
- `vmt_launcher/validator.py` - Input validation (125 lines)
- `vmt_launcher/__init__.py` - Package exports
- `launcher.py` - Entry point script

### Changed
- **requirements.txt**: Added PyQt5>=5.15.0 dependency
- **README.md**: Updated with GUI launcher quick start and features
- **Simulation.py**: Enhanced to support both legacy CSV and new SQLite logging
- **Documentation**: Restructured and consolidated into single-source guides

### Fixed

#### Logging System Bugs
- **Missing log_iteration method**: Added alias for backward compatibility
- **Snapshot frequency bug**: Fixed 0 value logging at every tick instead of disabling
- **NumPy integer storage**: Fixed serialization of numpy int64 as bytes instead of integers

### Documentation
- `PLANS/docs/NEW_LOGGING_SYSTEM.md` - Complete logging system guide (consolidated)
- `PLANS/docs/GUI_LAUNCHER_GUIDE.md` - Complete GUI guide (consolidated)
- `PLANS/docs/UTILITY_FUNCTION_DOCUMENTATION.md` - Documentation panel feature
- `PLANS/docs/UTILITY_DOCUMENTATION_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `RECENT_UPDATES_OVERVIEW.md` - Comprehensive overview of recent changes
- `CHANGELOG.md` - This file (starting version tracking)
- Updated `PLANS/DOCUMENTATION_INDEX.md` with new structure

### Performance
- **Logging**: 99.1% reduction in storage for standard logging
- **Logging**: 30-60x faster query and load times
- **GUI**: ~1.5s cold start, <100ms scenario list refresh

### Backward Compatibility
- **CLI workflow**: Completely unchanged, all existing commands work
- **Legacy CSV logging**: Still available via `use_legacy_logging=True`
- **Export to CSV**: Database runs can be exported to CSV format
- **All tests**: 54+ existing tests still pass

---

## [1.0.0] - 2025-10-11

### Added - Initial Production Release

#### Core Engine
- **Agent-based simulation** with spatial grid
- **CES utility functions** (including Cobb-Douglas)
- **Linear utility functions** (perfect substitutes)
- **Price search algorithm** for mutually beneficial trades
- **Bilateral barter** with compensating multi-lot rounding
- **Reservation pricing** (zero bid-ask spread)

#### Behavioral Systems
- **Foraging system** with distance-discounted utility-seeking
- **Resource regeneration** with cooldown mechanisms
- **Trade cooldown** to prevent futile re-targeting
- **Partner selection** with surplus-based matching
- **Movement system** with pathfinding

#### Technical Features
- **45 comprehensive tests** covering all systems
- **Pygame visualization** with interactive controls
- **YAML configuration** for scenarios
- **Enhanced telemetry** (CSV-based)
  - trades.csv
  - trade_attempts.csv
  - agent_snapshots.csv
  - decisions.csv
  - resource_snapshots.csv
- **Deterministic execution** (same seed → identical results)
- **Spatial indexing** for O(N) agent interactions
- **Performance optimized** for grids up to 100×100

#### Economic Features
- **MRS to discrete trade** gap solved via price search
- **Bootstrap requirement** for CES utilities documented
- **Complementary preferences** support heterogeneous agents
- **Gains from trade** observable through visualization

#### Documentation
- `PLANS/Planning-Post-v1.md` - Authoritative as-built specification
- `PLANS/V1_CHECKPOINT_REVIEW.md` - Implementation retrospective
- `PLANS/Big_Review.md` - Comprehensive evaluation
- `PLANS/docs/TELEMETRY_IMPLEMENTATION.md` - Enhanced logging
- `PLANS/docs/PRICE_SEARCH_IMPLEMENTATION.md` - Price discovery algorithm
- `PLANS/docs/TRADE_COOLDOWN_IMPLEMENTATION.md` - Cooldown mechanics
- `PLANS/docs/RESOURCE_REGENERATION_IMPLEMENTATION.md` - Regeneration system
- `PLANS/docs/CONFIGURATION.md` - Parameter reference
- `PLANS/DOCUMENTATION_INDEX.md` - Navigation guide
- `README.md` - Project overview and quick start

### Test Coverage
- **Core State**: 5 tests
- **Utilities**: 12 tests (CES, Linear, edge cases)
- **Scenarios**: 3 tests (YAML loading and validation)
- **Simulation**: 4 tests (initialization and determinism)
- **Foraging**: 3+ tests (movement, harvesting, utility-seeking)
- **Regeneration**: 8 tests (cooldown, growth, caps)
- **Trade Cooldown**: 4 tests (partner filtering, expiry)
- **Trade Rounding**: 2 tests (compensating multi-lot)
- **Reservations**: 5 tests (zero-safe bounds)
- **Total**: 45 tests, all passing ✅

### Performance Benchmarks
- **Grid Size**: Tested up to 100×100
- **Agents**: Tested up to 50 agents
- **Typical**: 32×32 grid with 3-10 agents runs at 60+ ticks/second

---

## Maintenance Guidelines

### When to Update This File

**For Every Release:**
1. Add a new version section at the top (under [Unreleased])
2. Move relevant items from [Unreleased] to the new version
3. Update the version number and date
4. Clear out the [Unreleased] section

**Version Numbering:**
- **Major (X.0.0)**: Breaking changes, major architecture changes
- **Minor (1.X.0)**: New features, backward-compatible additions
- **Patch (1.0.X)**: Bug fixes, documentation updates, minor tweaks

**Categories to Use:**
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

### Commit Message Format

Use conventional commits for easy changelog generation:

```
feat: add database logging system
fix: resolve numpy integer serialization bug
docs: update README with GUI launcher
perf: optimize spatial indexing queries
test: add trade cooldown test cases
```

### Example Update Process

```bash
# 1. After completing a feature
git commit -m "feat: add scenario templates library"

# 2. Update CHANGELOG.md under [Unreleased] > Added
# "- Scenario templates library with 10 pre-built examples"

# 3. When ready to release
# Move [Unreleased] content to new version section
# Update version in setup.py, __init__.py, etc.
# Commit and tag
git tag -a v1.2.0 -m "Version 1.2.0: Scenario templates"
git push --tags
```

### Changelog Best Practices

1. **User-focused**: Describe impact, not implementation
2. **Specific**: Include file names, function names when relevant
3. **Complete**: Don't skip minor but visible changes
4. **Organized**: Group related changes together
5. **Links**: Reference GitHub issues/PRs when applicable
6. **Breaking changes**: Clearly mark and explain migration path

### Review Checklist

Before releasing a new version:
- [ ] All changes since last release are documented
- [ ] Version number follows semver
- [ ] Date is correct
- [ ] Breaking changes are clearly marked
- [ ] Migration guide provided for breaking changes
- [ ] Links to relevant documentation are included
- [ ] Performance impacts are noted
- [ ] Backward compatibility is addressed

---

**Current Version:** 1.1.0  
**Last Updated:** October 12, 2025  
**Next Review:** When next feature is complete

