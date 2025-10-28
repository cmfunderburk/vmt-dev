# Phase 2a Merge Summary

Date: 2025-10-28

## Scope
Phase 2a delivers the Protocol Registry infrastructure, canonical protocol naming, baseline protocols, and schema/factory integration, plus documentation and tests.

## Implemented
- Protocol Registry System
  - `ProtocolMetadata`, `ProtocolRegistry`, `register_protocol` decorator
  - Helper functions: `list_all_protocols()`, `describe_all_protocols()`, `get_protocol_info()`
  - Crash-fast assertions in `vmt_engine/protocols/__init__.py` and per-subpackage `__init__.py`

- Canonical Protocol Names (no aliases)
  - Search legacy: `legacy_distance_discounted`
  - Matching random: `random_matching`
  - Bargaining split difference: `split_difference` (unchanged)
  - Names are consistent across YAML, registry, and telemetry

- Protocol Implementations (decorated and versioned)
  - Search: `LegacySearchProtocol` (distance-discounted), `RandomWalkSearch`
  - Matching: `LegacyMatchingProtocol` (three-pass), `RandomMatching`
  - Bargaining: `LegacyBargainingProtocol` (compensating block), `SplitDifference`

- Base Class Version Pattern
  - Class-level `VERSION` on base classes; instance `version` property proxies `VERSION`

- Factory + Schema Integration
  - `scenarios/protocol_factory.py` instantiates via registry; defaults updated to canonical names
  - `scenarios/schema.py` forces protocol imports and validates against registry listings

- Tests
  - `tests/test_protocol_registry.py` (registration, lookup, metadata, helpers, factory)
  - Updated existing tests and scenario fixtures to canonical names

- Documentation
  - `README.md` and `docs/protocols_10-27/README.md` updated to show canonical names and registry usage
  - `docs/tmp_plans/protocol_registry_implementation.md` aligned with actual implementation
  - `docs/structures/comprehensive_scenario_template.yaml` updated to canonical names

## Notable Changes / Migration
- Breaking (minor): YAML protocol names
  - Use `legacy_distance_discounted` (was `legacy`) and `random_matching` (was `random`)
  - Update any external/custom scenarios accordingly

## Key Files (selection)
- Registry: `src/vmt_engine/protocols/registry.py`
- Protocols: `src/vmt_engine/protocols/{search,matching,bargaining}/*.py`
- Imports/Asserts: `src/vmt_engine/protocols/__init__.py` and subpackage `__init__.py`
- Factory/Schema: `src/scenarios/protocol_factory.py`, `src/scenarios/schema.py`
- Tests: `tests/test_protocol_registry.py`, `tests/test_random_matching.py`, `tests/test_protocol_yaml_config.py`

## Validation
- Registry mechanics covered by tests; schema uses registry for validation
- Determinism discipline maintained (no unseeded RNG introduced)

## Follow-ups (tracked separately)
- Ensure any downstream docs/templates reference canonical names
- Optional: GUI protocol selector backed by `list_all_protocols()`


