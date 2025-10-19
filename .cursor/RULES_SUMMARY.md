# Cursor Rules Summary

Generated: October 19, 2025

## Overview

This directory contains comprehensive Cursor Rules to help AI coding agents work efficiently with the VMT codebase. These rules were created after thorough investigation, validation, and testing of all commands and workflows.

## Generated Rules (1,114 total lines)

### 1. **vmt-overview.mdc** (87 lines)
- **Type**: Always applied
- **Purpose**: Core project knowledge that should always be available
- **Contents**:
  - Critical setup requirements (venv, dependencies, testing)
  - The 7-phase tick cycle architecture
  - Determinism rules (mandatory sorting, no mid-tick mutations)
  - Type invariants (integers vs floats)
  - Architecture map and entry points
  - Versioning policy

### 2. **testing-workflow.mdc** (103 lines)
- **Type**: On-demand (description-based)
- **Purpose**: Testing, validation, and debugging guidelines
- **Contents**:
  - Pre-commit checklist
  - Test commands and configuration
  - **Critical database gotcha** (delete logs/telemetry.db for schema errors)
  - Running simulations for testing
  - Debugging failed tests
  - Adding new tests

### 3. **systems-development.mdc** (138 lines)
- **Type**: Glob-based (`src/vmt_engine/systems/*.py`)
- **Purpose**: Guidelines for modifying the 7 simulation phases
- **Contents**:
  - Phase order and file locations
  - Critical determinism rules with code examples
  - Integer math requirements
  - System-specific modification guidance
  - Common pitfalls to avoid
  - Adding new system features

### 4. **scenarios-telemetry.mdc** (216 lines)
- **Type**: Glob-based (`src/scenarios/*.py,scenarios/*.yaml,src/telemetry/*.py`)
- **Purpose**: Working with YAML scenarios and SQLite telemetry
- **Contents**:
  - Complete YAML schema reference
  - Creating new scenarios
  - Telemetry system architecture
  - Log levels (SUMMARY, STANDARD, DEBUG)
  - Database schema and modifications
  - Adding new telemetry
  - Performance considerations

### 5. **economics-utilities.mdc** (244 lines)
- **Type**: Glob-based (economics and trading files)
- **Purpose**: Economic logic, utility functions, trading algorithms
- **Contents**:
  - CES and Linear utility functions
  - Zero-inventory guard explanation
  - Reservation prices and quotes
  - Trading algorithm details (partner selection, price search)
  - Trade execution and cooldowns
  - Economic correctness checks
  - Testing economic logic
  - Parameter tuning guide

### 6. **gui-development.mdc** (322 lines)
- **Type**: Glob-based (GUI application files)
- **Purpose**: PyQt5 and Pygame GUI development
- **Contents**:
  - Three entry points (main.py, launcher.py, view_logs.py)
  - PyQt5 application structure
  - Pygame visualization
  - GUI development patterns
  - Threading for long simulations
  - Headless mode
  - Common GUI issues and solutions
  - Best practices

## Key Features

### Validated Information
- All commands have been tested and verified to work
- Common issues documented with proven solutions
- Expected test results specified (63 passed, 1 skipped)

### Critical Gotchas Documented
1. **Virtual environment name**: `venv` not `.venv`
2. **Database schema drift**: Must delete `logs/telemetry.db` after schema changes
3. **Import path**: Programmatic access requires `PYTHONPATH=.:src`
4. **Determinism requirements**: Explicit sorting and rounding rules

### Cross-Referenced
- Uses `[filename](mdc:path/to/filename)` format for file references
- Links to relevant documentation, tests, and implementation files
- Connects related concepts across different rule files

### Comprehensive Coverage
- **Architecture**: 7-phase system, determinism, spatial index
- **Economics**: Utility functions, trading, price search
- **Development**: Testing, scenarios, telemetry, GUI
- **Workflows**: Setup, testing, debugging, adding features

## Usage by AI Agents

### Always Applied
- `vmt-overview.mdc` provides baseline knowledge for every request

### Auto-Applied by File Type
- Editing systems → `systems-development.mdc`
- Editing scenarios/telemetry → `scenarios-telemetry.mdc`
- Editing economics → `economics-utilities.mdc`
- Editing GUI → `gui-development.mdc`

### On-Demand
- Testing issues → Agent can fetch `testing-workflow.mdc`
- Specific questions → Agent can query relevant rules

## Benefits

### For Coding Agents
1. **Reduced exploration time**: Critical info immediately available
2. **Fewer build failures**: Validated commands and workflows
3. **Better code quality**: Determinism and type requirements enforced
4. **Faster debugging**: Common issues documented with solutions

### For Developers
1. **Consistent guidance**: Same information available to all agents
2. **Validated workflows**: Commands proven to work
3. **Comprehensive coverage**: All major development areas covered
4. **Easy maintenance**: Single-file updates propagate to all agents

## Maintenance

These rules should be updated when:
- Project structure changes significantly
- New major systems are added
- Testing requirements change
- Common issues/gotchas are discovered
- Dependencies are updated

Last validated: October 19, 2025 with Python 3.12.3, 63 passing tests.

