## Effects and Systems

### Effects
- Defined in `src/vmt_engine/protocols/base.py`.
- Represent intended actions: movement, trade, resource operations.
- Are immutable data the engine can validate and apply.

### Systems
- Live in `src/vmt_engine/systems/` and implement phase logic.
- Responsibilities:
  - Validate incoming Effects for the phase.
  - Enforce ordering (sorted by agent IDs, pair IDs).
  - Apply changes to `State` deterministically.

### State mutation rule
- All state changes happen inside systems when applying Effects.
- Never mutate `agent.position`, `agent.inventory`, or `world.grid` in protocols.

### Phase responsibilities (high level)
- Movement system: executes `MoveEffect`s.
- Foraging system: applies resource harvest/regeneration Effects.
- Trading system: runs price/quantity search, applies `TradeEffect`s.

### Common pitfalls
- Silent direct state mutation from within a protocol.
- Iterating over dicts/sets without sorting.
- Floating point accumulation for money—prefer integer minor units.


