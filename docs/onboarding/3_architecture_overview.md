## Architecture Overview

### Core principles
- **Determinism**: Same seed ⇒ identical outcomes across runs.
- **Protocol → Effect → State**: Decisions produce Effects; the engine validates/applies them to update State.
- **Phase discipline**: Agent decisions in odd phases; world updates in even phases.

### 7-phase tick cycle (engine-level contract)
1. Resource regeneration
2. Movement decisions → MoveEffects
3. Movement execution
4. Foraging/mining decisions → ResourceEffects
5. Trade negotiations → TradeEffects
6. Trade execution and inventory updates
7. Consumption and utility calculation (housekeeping)

See `docs/2_technical_manual.md` for a deeper walkthrough.

### Determinism requirements (must-follow)
- Use only seeded RNGs (`self.rng` in agents, `world.rng` in engine). Never use `random`, `numpy.random` globals, time, or system state as randomness.
- Always sort collections before iteration (e.g., `sorted(agents, key=lambda a: a.id)`). Never iterate over unordered sets/dicts.
- Monetary values: round consistently (2 decimals) or store integer minor units.
- All state updates happen via Effects in phase transitions. Never mutate `world.grid`, `agent.inventory`, or positions directly.

### Module structure
- Protocols: `src/vmt_engine/protocols/` (market mechanisms)
- Systems: `src/vmt_engine/systems/` (phase implementations)
- Effects: `src/vmt_engine/protocols/base.py`
- Core state: `src/vmt_engine/core/`
- Telemetry: `src/telemetry/`

### How pieces fit
- Protocols read a read-only `WorldView` and return Effects.
- Engine validates Effects (ordering, feasibility) and applies them deterministically.
- Telemetry logs states, trades, and events for analysis.


