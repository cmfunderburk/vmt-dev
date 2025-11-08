# BaseAgent / SpatialAgent Migration Plan

## Objectives
- Introduce a lean `BaseAgent` shared across Game Theory and future Neoclassical tooling.
- Move spatial-only state and behavior into a new `SpatialAgent` subclass without breaking existing simulations.
- Preserve determinism and telemetry fidelity throughout the transition.

## Phase 0 – Pre-Work (Detailed Checklist)
1. **Map Agent Usage**
   - Run static search to list modules importing `Agent` (`src/vmt_engine`, `tests`, `scripts`).
   - Categorize each usage: construction, attribute access, type annotation, or subclassing.
   - Record findings in a temporary table (module, purpose, spatial dependency) to identify hotspots.
2. **Audit Telemetry & Persistence**
   - Inspect telemetry writer modules for direct `Agent` field serialization (inventory, position, quotes).
   - Verify SQLite schema fields in `logs/telemetry.db` align with the planned split; note any assumptions about spatial data always existing.
3. **Scenario Pipeline Review**
   - Trace scenario loading: YAML → `scenarios.loader` → agent instantiation.
   - Confirm no implicit reliance on class name strings; identify factory points needing updates.
4. **Protocol & System Contracts**
   - Review search, matching, bargaining, and movement systems for direct field access (e.g., `agent.pos`, `agent.quotes`).
   - Document which systems only need economic data versus spatial state.
5. **Testing Inventory**
   - List pytest modules referencing `Agent`; flag determinism, protocol, and integration suites for focused regression.
6. **Plan Communication**
   - Update stakeholders/planning docs with summary of findings before Phase 1 starts (ensures agreement on split scope).

## Phase 1 – Define `BaseAgent` (Detailed Checklist)
1. **Design Contract**
   - Specify exact fields/methods for `BaseAgent` based on Phase 0 findings.
   - Draft docstring detailing intended usage (Game Theory, Neoclassical, analytics).
2. **Create Module**
   - Add `agent_base.py` (or equivalent) under `src/vmt_engine/core/` with `BaseAgent` dataclass.
   - Implement validations (ID non-negative) and integrate existing `Inventory` quantization logic.
3. **Utility Hooks**
   - Implement minimal utility evaluation methods (`compute_utility`, placeholder for `optimal_bundle`) with deterministic behavior.
   - Provide optional hooks for quotes/reservation prices if required by non-spatial contexts (likely getters/setters or abstract placeholders).
4. **Dependency Wiring**
   - Ensure `BaseAgent` imports avoid pulling in spatial modules to keep it lightweight (core state, utility interfaces only).
   - Decide whether to expose `BaseAgent` via `core/__init__.py` for external modules.
5. **Unit Tests**
   - Create targeted tests (e.g., `tests/core/test_base_agent.py`) covering construction, inventory updates, and utility evaluation passthrough.
   - Include determinism guard (e.g., repeated utility computation yields identical results) if RNG hooks present.
6. **Documentation Update**
   - Append summary of `BaseAgent` interface to planning document and, once implemented, update technical manual references.
7. **Review & Sign-off**
   - Present Phase 1 artifact (code + tests + doc summary) for review before initiating Phase 2.

## Phase 2 – Refactor Existing Agent to `SpatialAgent`
- Rename current `Agent` class to `SpatialAgent` and inherit from `BaseAgent`.
- Move spatial attributes (`pos`, `vision_radius`, etc.), runtime caches, and barter quotes into `SpatialAgent`.
- Update module exports so legacy imports (`from core.agent import Agent`) either alias `SpatialAgent` temporarily or raise clear migration errors.
- Adjust serialization/telemetry hooks to use `SpatialAgent` where spatial data is required.

## Phase 3 – Update Callers
- Update engine systems (perception, decision, movement) to import `SpatialAgent` explicitly.
- Adjust matching/bargaining protocols that rely on spatial state to expect `SpatialAgent`.
- Ensure helper factories (`ProtocolContext`, scenario loaders) construct `SpatialAgent` instances.

## Phase 4 – Introduce Game Theory Usage
- Modify Game Theory modules to consume `BaseAgent` (or lightweight wrappers) without spatial dependencies.
- Provide adapter utilities if Game Theory components still need quotes or other optional data.
- Draft determinism tests covering both spatial simulations and new Game Theory workflows (seeded runs, Exchange Engine determinism).

## Phase 5 – Clean-Up & Documentation
- Remove temporary aliases once downstream code references `SpatialAgent` directly.
- Update documentation (`PROJECT_STATUS_REVIEW.md`, Stage 3 plan) to reflect new class hierarchy.
- Regenerate API docs/type stubs if maintained elsewhere.

## Validation Checklist
- `pytest` passes with determinism tests focused on both tracks.
- Sample scenario runs produce identical telemetry vs. pre-refactor baselines.
- Game Theory modules instantiate `BaseAgent` successfully without spatial baggage.
- No residual imports of old `Agent` symbol remain (enforce via `grep`/lint).
