# Cursor Rules Summary

Generated: October 20, 2025

## Overview

This directory contains comprehensive Cursor Rules to help AI coding agents work efficiently with the VMT codebase. These rules provide validated workflows, critical invariants, and best practices for all major development areas.

## Generated Rules (1,619 total lines across 14 files)

### Core Rules

#### 1. **core-invariants.mdc** (104 lines)
- **Type**: Always applied (critical baseline knowledge)
- **Purpose**: Inviolable requirements that maintain determinism and correctness
- **Contents**:
  - Determinism rules: sorted loops, no mid-tick mutations, round-half-up rounding
  - Type invariants: integer vs float field requirements
  - The 7-phase tick cycle (sacred order)
  - Spatial query requirements (always use SpatialIndex)
  - Movement tie-breakers
  - Backward compatibility requirements
  - Testing requirements
  - Critical database gotcha (delete logs/telemetry.db for schema errors)
  - Environment setup (venv, PYTHONPATH)

#### 2. **vmt-overview.mdc** (55 lines)
- **Type**: On-demand (description-based)
- **Purpose**: High-level project orientation and quick reference
- **Contents**:
  - Project architecture map
  - Entry points (CLI, GUI, programmatic)
  - Key algorithms (trading, movement, quotes, spatial queries)
  - Versioning policy (date-based, no SemVer)
  - Documentation hub

### Development Workflow Rules

#### 3. **testing-workflow.mdc** (90 lines)
- **Type**: On-demand (description-based)
- **Purpose**: Testing, validation, and debugging guidelines
- **Contents**:
  - Pre-commit checklist
  - Test commands and configuration
  - Running simulations for testing
  - Common test scenarios
  - Debugging failed tests (includes database gotcha)
  - Adding new tests

#### 4. **feature-development-checklist.mdc** (60 lines)
- **Type**: On-demand (description-based)
- **Purpose**: Systematic workflow for adding new features
- **Contents**:
  - Pre-development planning
  - Implementation guidelines
  - Schema & telemetry updates
  - Testing requirements
  - Documentation updates
  - Pre-commit final checklist
  - Feature-specific notes (economic, spatial, GUI)
  - Common pitfalls to avoid

#### 5. **refactoring-and-deprecation.mdc** (312 lines)
- **Type**: Glob-based (applies to all src/ and tests/ Python files)
- **Purpose**: Safe refactoring, deprecation, and code removal
- **Contents**:
  - Multi-step deprecation workflow
  - Safe refactoring checklist
  - Specific refactoring patterns (renaming, signature changes, module moves)
  - Finding dead code strategies
  - High-risk refactoring areas
  - Database schema changes (special case)
  - Documentation update checklist
  - Code review self-checklist
  - Emergency rollback procedures

### System-Specific Rules

#### 6. **systems-development.mdc** (50 lines)
- **Type**: Glob-based (`src/vmt_engine/systems/*.py`)
- **Purpose**: Guidelines for modifying the 7 simulation phases
- **Contents**:
  - Phase order and file locations
  - Critical determinism rules with examples
  - Integer math requirements
  - System-specific modification guidance
  - Adding new system features
  - Common pitfalls

#### 7. **economics-utilities.mdc** (43 lines)
- **Type**: Glob-based (economics and trading files)
- **Purpose**: Economic logic, utility functions, trading algorithms
- **Contents**:
  - Utility functions (CES and Linear)
  - Zero-inventory guard explanation
  - Reservation prices and quotes
  - Trading algorithm essentials
  - Economic correctness requirements
  - Testing pointers
  - Parameter tuning guide

#### 8. **scenarios-telemetry.mdc** (295 lines)
- **Type**: Glob-based (`src/scenarios/*.py`, `scenarios/*.yaml`, `src/telemetry/*.py`)
- **Purpose**: Working with YAML scenarios and SQLite telemetry
- **Contents**:
  - Complete YAML schema reference with examples
  - **Strict requirements for test scenarios**: complementary pairing algorithm
  - Creating new scenarios
  - Telemetry system architecture
  - Log levels (STANDARD, DEBUG, OFF)
  - Database schema and modifications
  - Adding new telemetry
  - Performance considerations
  - Common mistakes (includes critical test scenario requirements)

#### 9. **gui-development.mdc** (79 lines)
- **Type**: Glob-based (GUI application files)
- **Purpose**: PyQt5 and Pygame GUI development
- **Contents**:
  - Three entry points (main.py, launcher.py, view_logs.py)
  - Module organization
  - Launcher features (including spec for auto-generate diverse agents)
  - Log viewer features
  - Pygame visualization
  - PyQt5 patterns and tips
  - Troubleshooting common issues

### Money System Rules

#### 10. **money-guide.mdc** (198 lines)
- **Type**: On-demand (description-based)
- **Purpose**: Top-level guide for money system implementation
- **Contents**:
  - Links to all money-related rules and documents
  - Phase checklists (remaining: phases 3-6)
  - Completed phases: Phase 1 ✅ and Phase 2 ✅
  - Implementation workflow (starting new phases)
  - Critical invariants to maintain
  - Common development tasks
  - Testing commands
  - Code review checklist
  - Implementation status (as of October 20, 2025)

#### 11. **money-implementation.mdc** (186 lines)
- **Type**: Glob-based (money system files)
- **Purpose**: Architectural decisions and implementation details
- **Contents**:
  - Frozen core architecture decisions
  - Money representation (integer M, conservation)
  - Price aggregation strategy
  - Trading rules
  - Mode system architecture (temporal × type control)
  - Exchange regimes (barter_only/money_only/mixed/mixed_liquidity_gated)
  - Implementation phases overview (Phases 1-2 ✅ complete)
  - Critical invariants
  - Testing requirements
  - Pedagogical goals
  - Code organization and key algorithms
  - Error handling

#### 12. **money-testing.mdc** (64 lines)
- **Type**: Glob-based (money test files)
- **Purpose**: Testing requirements for money implementation
- **Contents**:
  - Testing philosophy (phased gates)
  - Phase gates (Phases 1-2 ✅ complete, 152 tests passing)
  - Determinism requirements
  - Required test scenarios
  - Performance targets
  - Testing commands
  - Validation checklist per phase

#### 13. **money-telemetry.mdc** (47 lines)
- **Type**: Glob-based (telemetry files and money schema docs)
- **Purpose**: Database schema extensions for money system
- **Contents**:
  - Additive schema extensions
  - Logging requirements (conditional based on regime)
  - Query patterns for analysis
  - Performance and indexing
  - Migration strategy
  - Validation checks

#### 14. **money-pedagogical.mdc** (36 lines)
- **Type**: Glob-based (scenario files and documentation)
- **Purpose**: Teaching objectives and demo requirements
- **Contents**:
  - Teaching objectives
  - Required demo scenarios (5 demos)
  - Visualization requirements
  - Resources for instructors
  - Best practices for educational use

## Key Features

### Validated Information
- All commands tested and verified to work
- Common issues documented with proven solutions
- Current test results: **152 tests passing** (57 new money tests added in Phase 2)
- Python version: **3.11.2**

### Critical Gotchas Documented
1. **Virtual environment name**: `venv` not `.venv`
2. **Database schema drift**: Must delete `logs/telemetry.db` after schema changes
3. **Import path**: Programmatic access requires `PYTHONPATH=.:src`
4. **Determinism requirements**: Explicit sorting and rounding rules
5. **Test scenario requirements**: Every agent must have unique utility function (complementary pairing)
6. **Spatial parameters in tests**: ALWAYS use `interaction_radius: 1` and `move_budget_per_tick: 1`

### Cross-Referenced
- Uses `[filename](mdc:path/to/filename)` format for file references
- Links to relevant documentation, tests, and implementation files
- Connects related concepts across different rule files

### Comprehensive Coverage
- **Core**: Invariants, determinism, type safety, 7-phase architecture
- **Economics**: Utility functions, trading, price search, money system
- **Development**: Testing, scenarios, telemetry, refactoring
- **GUI**: PyQt5 launcher, log viewer, Pygame visualization
- **Workflows**: Setup, testing, debugging, adding features

## Usage by AI Agents

### Always Applied
- `core-invariants.mdc` provides critical requirements for every edit

### Auto-Applied by File Type (Glob-Based)
- Editing `src/vmt_engine/systems/*.py` → `systems-development.mdc`
- Editing scenarios/telemetry → `scenarios-telemetry.mdc`
- Editing economics code → `economics-utilities.mdc`
- Editing GUI code → `gui-development.mdc`
- Editing money system code → `money-implementation.mdc`
- Editing Python files (refactoring) → `refactoring-and-deprecation.mdc`

### On-Demand (Description-Based)
- Testing questions → `testing-workflow.mdc`
- Feature planning → `feature-development-checklist.mdc`
- Money system work → `money-guide.mdc`, `money-testing.mdc`, etc.
- Project orientation → `vmt-overview.mdc`

## Major Milestones

### Phase 1: Money Infrastructure ✅ COMPLETE
- Added money fields with backward compatibility
- Extended Inventory with M field
- Extended telemetry schema
- All legacy scenarios still work identically

### Phase 2: Monetary Exchange ✅ COMPLETE (October 19, 2025)
- Implemented quasilinear money utility
- Added money-aware utility API
- Generic matching algorithm for all exchange pairs (A↔M, B↔M, A↔B)
- Regime-aware trading (barter_only/money_only/mixed)
- **57 new tests added** (152 total, up from 95 baseline)
- Test scenario `money_test_basic.yaml` created
- Conservation laws enforced
- Backward compatibility maintained (100%)

### Phases 3-6: In Progress
- **Phase 3**: KKT λ estimation (next)
- **Phase 4**: Mixed regimes
- **Phase 5**: Liquidity gating
- **Phase 6**: Polish and documentation

## Benefits

### For Coding Agents
1. **Reduced exploration time**: Critical information immediately available
2. **Fewer build failures**: Validated commands and workflows
3. **Better code quality**: Determinism and type requirements enforced
4. **Faster debugging**: Common issues documented with solutions
5. **Context-appropriate guidance**: Right rules activated for the code being edited

### For Developers
1. **Consistent guidance**: Same information available to all agents
2. **Validated workflows**: Commands proven to work
3. **Comprehensive coverage**: All major development areas covered
4. **Easy maintenance**: Single-file updates propagate to all agents
5. **Progress tracking**: Clear milestones and completion status

## Maintenance

These rules should be updated when:
- Project structure changes significantly
- New major systems are added
- Testing requirements change
- Common issues/gotchas are discovered
- Dependencies are updated
- Major implementation phases complete (update status)

Last validated: October 20, 2025 with Python 3.11.2, 152 passing tests.
Last updated: October 20, 2025 after Phase 2 completion.
