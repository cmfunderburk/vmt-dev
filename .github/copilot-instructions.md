# VMT (Visualizing Microeconomic Theory) - AI Agent Instructions

## Project Mission
VMT is a spatial agent-based simulation for researching how market phenomena **emerge** from micro-level interactions. Rather than assuming equilibrium, it demonstrates how search protocols, matching algorithms, and bargaining mechanisms produce (or fail to produce) price convergence. This is fundamentally about **institutional comparative analysis** in economics.

## Critical: Determinism is Non-Negotiable
Every simulation run with the same seed **must** produce identical results. This is the foundation of scientific validity.

**Mandatory practices:**
- **RNG:** Use ONLY seeded generators (`self.rng` in agents, `world.rng` in engine). NEVER `random.random()`, `numpy.random`, or time-based randomness
- **Iteration order:** Always sort before iterating: `for agent in sorted(agents, key=lambda a: a.id)`. NEVER iterate over sets or dict.keys() directly
- **Floating point:** Round money to 2 decimals: `round(value, 2)`. Store as integers (cents) when possible
- **Verification:** Run `pytest tests/` after changes. All tests must pass.

## Architecture: Protocol → Effect → State Pattern
This is the **fundamental design** - no exceptions.

**The flow:**
1. **Protocols** make decisions from read-only `WorldView` snapshots
2. **Effects** declare intended actions (never mutate state directly)
3. **Engine** validates and applies effects in deterministic order

**Example (CORRECT):**
```python
# Decision phase - protocol returns effects
effects.append(MoveEffect(agent_id=agent.id, new_position=(x, y)))

# NEVER do this:
# agent.position = (x, y)  # Direct mutation is forbidden
```

**Effect types** (see `src/vmt_engine/protocols/base.py`):
- `SetTarget`, `ClaimResource`, `ReleaseClaim` - target selection
- `Pair`, `Unpair` - agent pairing
- `Move` - movement
- `Trade` - exchange execution
- `Harvest` - resource collection

## 7-Phase Tick Cycle
Each tick follows this exact sequence (see `src/vmt_engine/simulation.py`):

0. **Resource Regeneration** - Cells regenerate after cooldown
1. **Perception** - Agents observe frozen world snapshot
2. **Decision** - Search → matching → target selection (produces effects)
3. **Movement** - Movement effects applied
4. **Trading** - Bargaining → trade effects applied
5. **Foraging** - Harvest effects applied
6. **Housekeeping** - Quote updates, telemetry logging

**Phase discipline:** Odd phases = decisions, even phases = state updates. Never mix.

## Module Structure
```
src/vmt_engine/
├── core/           # Grid, Agent, Inventory, spatial primitives
├── econ/           # Utility functions (5 types: CES, Linear, Quadratic, Translog, Stone-Geary)
├── protocols/      # Market mechanisms (search, matching, bargaining)
│   ├── base.py    # Effect classes & protocol interfaces
│   ├── search/    # LegacySearchProtocol (distance-discounted utility search)
│   ├── matching/  # LegacyMatchingProtocol (three-pass mutual consent + greedy)
│   └── bargaining/ # LegacyBargainingProtocol (compensating blocks)
├── systems/        # Phase implementations (perception, movement, trading, etc.)
└── simulation.py   # Main orchestration
```

## Key Economic Concepts

**Utility Functions** (`src/vmt_engine/econ/utility.py`):
- All implement money-aware API: `u_goods(A, B)`, `mu_A(A, B)`, `mu_B(A, B)`
- Quasilinear utility: `U_total = U_goods(A, B) + λ·M`
- Zero-inventory guard: Add epsilon to prevent MRS singularities in ratio calculations

**Exchange Regimes** (`exchange_regime` parameter):
- `barter_only` - Only A↔B trades
- `money_only` - Only A↔M and B↔M trades
- `mixed` - All trade types allowed

**Three-Pass Matching Algorithm** (see `docs/2_technical_manual.md` lines 40-60):
1. **Pass 1:** Each agent ranks visible neighbors by distance-discounted surplus
2. **Pass 2:** Mutual consent pairing (both agents list each other as #1)
3. **Pass 3:** Greedy surplus matching for unpaired agents

## Testing Requirements
Every new feature **must** have tests before completion.

**Test structure:**
```python
def test_feature_normal_case():
    """Test expected behavior with typical inputs."""
    pass

def test_feature_edge_case():
    """Test boundaries (empty, zero, max values)."""
    pass

def test_feature_validates_input():
    """Test invalid inputs raise appropriate errors."""
    with pytest.raises(ValueError):
        function_name(invalid_input)
```

**Economic validation:**
- Trades must be individually rational (ΔU > 0 for both agents)
- Conservation laws hold (total resources unchanged)
- Prices non-negative and properly rounded

**Run tests:** `pytest tests/` (all must pass)
**Verify determinism:** Run simulation twice with same seed, compare telemetry DBs

## Working with Scenarios
Scenarios are YAML files defining simulation parameters (see `scenarios/*.yaml`).

**Key sections:**
- `N`: Grid size
- `agents`: Number of agents
- `initial_inventories`: Starting goods {A, B} per agent
- `utilities.mix`: Distribution of utility functions across agents
- `params`: Simulation parameters (vision_radius, dA_max, exchange_regime, etc.)

**Test scenarios:** Use `scenarios/three_agent_barter.yaml` for quick validation

## Development Workflows

**Run simulation:**
```bash
python launcher.py  # GUI (recommended)
python main.py scenarios/three_agent_barter.yaml 42  # CLI with seed
```

**Run tests:**
```bash
pytest tests/  # All tests
pytest tests/test_specific.py  # Single file
pytest -xvs  # Stop on first failure, verbose output
```

**Check determinism:**
```bash
# Run twice, compare databases
python main.py scenarios/three_agent_barter.yaml 42
python main.py scenarios/three_agent_barter.yaml 42
# Manually compare logs/*.db files or use scripts/compare_telemetry_snapshots.py
```

## Protocol Implementation (Future Work)
When implementing new protocols (Phase 2+):

1. **Extend base class** from `src/vmt_engine/protocols/base.py`:
   - `SearchProtocol` → implement `execute(worldview) -> list[Effect]`
   - `MatchingProtocol` → implement `execute(worldview) -> list[Effect]`
   - `BargainingProtocol` → implement `execute(worldview) -> list[Effect]`

2. **Return effects, never mutate state**

3. **Register with ProtocolRegistry** using `@ProtocolRegistry.register` decorator

4. **Document economic mechanism** in docstring (what market behavior does this implement?)

**Example structure:**
```python
@ProtocolRegistry.register
class RandomSearchProtocol(SearchProtocol):
    """Random walk search (zero-information baseline)."""
    
    protocol_type = "search"
    protocol_name = "random_search"
    version = "2025.10.27"
    
    def execute(self, worldview: WorldView) -> list[Effect]:
        effects = []
        for agent_id in worldview.agent_ids:
            # Random target selection logic
            target = random_position(worldview.rng)
            effects.append(SetTarget(
                agent_id=agent_id,
                target=target,
                protocol_name=self.protocol_name,
                tick=worldview.tick
            ))
        return effects
```

## Documentation Locations
- **Big picture:** `docs/BIGGEST_PICTURE/vision_and_architecture.md` - Strategic vision, research agenda
- **Technical details:** `docs/2_technical_manual.md` - 7-phase cycle, algorithms, money system
- **Project overview:** `docs/1_project_overview.md` - Quick start, philosophy
- **Legacy rules:** `.cursor/rules/` - Historical AI agent instructions (merged into this file)

## Common Pitfalls to Avoid
❌ Direct state mutation (use effects)  
❌ Unseeded randomness (breaks determinism)  
❌ Unordered iteration (breaks determinism)  
❌ Assuming equilibrium exists (the point is to discover when it emerges)  
❌ Testing with only one utility function (heterogeneity matters)  
❌ Ignoring failed tests (all tests must pass)  

## When Stuck
1. Check `docs/2_technical_manual.md` for algorithm details
2. Read existing protocol implementations in `src/vmt_engine/protocols/`
3. Look at test cases in `tests/` for usage examples
4. Review vision doc for "why" behind design decisions
