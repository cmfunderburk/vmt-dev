# BaseAgent / SpatialAgent Migration Plan

## Objectives
- Introduce a lean `BaseAgent` shared across Game Theory and future Neoclassical tooling.
- Move spatial-only state and behavior into a new `SpatialAgent` subclass without breaking existing simulations.
- Preserve determinism and telemetry fidelity throughout the transition.

## Phase 0 – Pre-Work
- **Dependency Audit**: catalogue imports and type hints referencing `Agent` across `src/vmt_engine/` and `tests/`.
- **Telemetry Schema Review**: confirm which agent fields are persisted in `logs/telemetry.db`; update documentation if schema stays unchanged.
- **Scenario Loader Check**: identify construction points (e.g., `scenarios/loader.py`) to ensure they can swap in `SpatialAgent`.

## Phase 1 – Define `BaseAgent`
- Create `BaseAgent` dataclass in `src/vmt_engine/core/agent_base.py` (or similar) with identity, inventory, utility references, and minimal economic helpers.
- Add shared validation logic (non-negative IDs, inventory quantization) and reusable helper methods for utility evaluation.
- Write unit tests focused on `BaseAgent` invariants (construction, inventory updates, utility evaluations).

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
