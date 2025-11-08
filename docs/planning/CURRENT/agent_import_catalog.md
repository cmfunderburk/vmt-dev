# Agent Import Catalog

## Method
- Searched repository with `rg "import Agent"` scoped to `/src`, `/tests`, and `/scripts`.
- Reviewed each module to summarize how the current `Agent` class is consumed.
- Distinguish between runtime imports and `TYPE_CHECKING`-only annotations, noting spatial dependencies when present.

## Findings
| Module Path | Import Style | Primary Usage | Spatial Dependency? | Notes |
| --- | --- | --- | --- | --- |
| `src/vmt_engine/simulation.py` | `from .core import Grid, Agent, Inventory, SpatialIndex` (runtime) | Instantiates agents during scenario load; passes full state to systems | ✔️ | Must switch to constructing `SpatialAgent` in Phase 2; central choke point |
| `src/vmt_engine/core/__init__.py` | `from .agent import Agent` (runtime re-export) | Provides canonical import path for rest of codebase | ✔️ | Will need to re-export `SpatialAgent` (and possibly `BaseAgent`) post-refactor |
| `src/vmt_engine/core/spatial_index.py` | `if TYPE_CHECKING: from .agent import Agent` | Type hints for helper signatures | ✔️ | No runtime dependency; adjust annotations after split |
| `src/vmt_engine/protocols/context.py` | `if TYPE_CHECKING: from ..core.agent import Agent` | Annotates `ProtocolContext.agents` dict | ✔️ | Matching protocols expect full spatial/economic state; confirm interface against `BaseAgent` plan |
| `src/vmt_engine/protocols/context_builders.py` | `if TYPE_CHECKING: from ..core.agent import Agent` | Builds `WorldView`/`ProtocolContext` from live agents | ✔️ | Consumes position, quotes, pairing, caches; high-impact consumer |
| `src/vmt_engine/systems/decision.py` | `if TYPE_CHECKING: from ..core import Agent` | Orchestrates search/matching; manipulates pairing, targets | ✔️ | Heavy use of spatial flags (`paired_with_id`, `target_pos`, etc.) |
| `src/vmt_engine/systems/matching.py` | `if TYPE_CHECKING: from ..core import Agent` | Surplus heuristics, trade candidate generation | ✔️ | Reads quotes, inventories, cooldowns; ensure helper signatures updated |
| `src/vmt_engine/systems/trading.py` | `if TYPE_CHECKING: from ..core import Agent` | Negotiation orchestration; applies trade/unpair effects | ✔️ | Uses positions for distance checks; direct agent tuple passed to protocols |
| `src/vmt_engine/game_theory/bargaining/base.py` | `if TYPE_CHECKING: from ...core import Agent` | Abstract method signature for `negotiate`/`on_timeout` | ⚠️ (assumed) | Contract should migrate to `BaseAgent`-compatible typing |
| `src/vmt_engine/game_theory/bargaining/compensating_block.py` | `if TYPE_CHECKING: from ...core import Agent` | Implements barter search; reads inventory, utility, quotes | ✔️ | Needs compatibility layer if `BaseAgent` omits spatial fields |
| `src/vmt_engine/game_theory/bargaining/split_difference.py` | `if TYPE_CHECKING: from ...core import Agent` | Stub protocol returning `Unpair` | ❌ (stub) | Update annotation once Base/Spatial split lands |
| `src/vmt_engine/game_theory/bargaining/take_it_or_leave_it.py` | `if TYPE_CHECKING: from ...core import Agent` | Stub protocol returning `Unpair` | ❌ (stub) | Same as above |
| `src/vmt_engine/systems/trade_evaluation.py` | `if TYPE_CHECKING: from ..core import Agent` | Trade potential heuristics; converts tuples to effects | ✔️ | Reads quotes/inventory extensively |
| `src/vmt_engine/systems/_trade_attempt_logger.py` | `if TYPE_CHECKING: from ..core import Agent` | Telemetry helper capturing pre/post-trade state | ✔️ | Logging expects spatial/economic fields |
| `src/vmt_engine/systems/foraging.py` | `if TYPE_CHECKING: from ..core import Agent` | Forage execution mutating inventory, commitments | ✔️ | Strong spatial coupling |
| `src/vmt_engine/systems/movement.py` | `if TYPE_CHECKING: from ..core import Agent` | Movement step computation | ✔️ | Depends on `pos`, `target_pos`, pairing state |
| `src/vmt_engine/systems/perception.py` | `if TYPE_CHECKING: from ..core import Agent` | Builds perception caches with neighbor positions/quotes | ✔️ | Requires spatial info |
| `src/vmt_engine/systems/quotes.py` | `if TYPE_CHECKING: from ..core import Agent` | Computes/refreshes quotes | ⚠️ (economic) | Needs inventory + utility; could move to `BaseAgent` if quotes stay higher-level |
| `src/vmt_pygame/renderer.py` | `if TYPE_CHECKING: from vmt_engine.core import Agent` | UI rendering of positions, trades, quotes | ✔️ | Will eventually need to target `SpatialAgent` |
| `src/telemetry/db_loggers.py` | `if TYPE_CHECKING: from vmt_engine.core import Agent` | Persists agent snapshots/trades with spatial + economic fields | ✔️ | Schema depends on spatial fields; assess impact before refactor |
| `tests/helpers/builders.py` | `from vmt_engine.core import Agent, Inventory` (runtime) | Factory for constructing agents in tests | ✔️ | Test helpers must instantiate `SpatialAgent` or a shim |
| `tests/test_trade_cooldown.py` | `from vmt_engine.core import Agent, Inventory` (runtime) | Unit tests manipulating cooldown logic | ✔️ | Direct `Agent` construction; will need update post-split |

Legend: ✔️ = explicitly uses spatial fields; ⚠️ = primarily economic but verify expectations; ❌ = stub / not yet implemented.

## Observations
- Runtime imports concentrate in `Simulation` (construction) and test helpers; these are the first refactor targets.
- Most other modules rely on `TYPE_CHECKING` imports but still assume access to spatial fields at runtime via instances provided by `Simulation`.
- Telemetry and UI layers depend on spatial attributes for reporting; schema review needed before altering agent structure.
- Game Theory protocols currently expect full spatial agents even though they conceptually need only economic data, reinforcing the case for `BaseAgent` introduction.
