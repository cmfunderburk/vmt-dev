## Glossary

- **Effect**: An immutable intent (e.g., move, trade) produced by a protocol and applied by a system.
- **WorldView**: Read-only snapshot given to protocols for decision-making.
- **State**: Mutable engine state; updated only by systems when applying Effects.
- **Tick**: One discrete simulation time step comprising seven phases.
- **Exchange Regime**: Allowed exchange pairs (barter_only, money_only, mixed).
- **Mode**: Temporal control over which activities are active (forage, trade, both) during a tick range.
- **Reservation Bounds**: Price bounds derived from marginal utilities.
- **Telemetry**: SQLite logs capturing state and events for analysis.
- **Determinism**: Same seed yields identical outcomes across runs.


