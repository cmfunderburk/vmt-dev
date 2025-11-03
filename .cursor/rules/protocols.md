# Protocol Development Rules

Protocols define swappable institutional mechanisms. Follow these patterns for consistency.

## Protocol Template

```python
from vmt_engine.protocols import (
    ProtocolBase, register_protocol, ProtocolContext, Effect
)

@register_protocol("my_protocol_name", "category")  # category: search|matching|bargaining
class MyProtocol(ProtocolBase):
    """
    Brief description of institutional mechanism.
    
    Economic Properties:
    - What behavior does this represent?
    - What are the strategic implications?
    
    Implementation:
    - Key algorithm steps
    - Complexity: O(?)
    """
    
    def __init__(self, **config):
        """Optional config parameters."""
        super().__init__()
        self.param = config.get('param', default_value)
    
    def execute(self, context: ProtocolContext) -> list[Effect]:
        """
        Execute protocol logic and return effects.
        
        Args:
            context: Immutable world snapshot
            
        Returns:
            List of Effect objects to apply
        """
        # 1. Read from context (never mutate)
        agent = context.world_view.agents[context.agent_id]
        neighbors = context.world_view.spatial_index.query_radius(
            agent.pos, radius=agent.vision_radius
        )
        
        # 2. Make decisions
        # ... protocol logic ...
        
        # 3. Return effects (declarative)
        return [
            SetTarget(agent_id=context.agent_id, target_pos=target),
            # ... other effects
        ]
```

## Domain Organization

**Search protocols** → `src/vmt_engine/agent_based/search/`
- How agents find trading partners
- Example: `myopic.py`, `random_walk.py`

**Matching protocols** → `src/vmt_engine/game_theory/matching/`
- How pairs form from available agents
- Example: `greedy.py`, `random.py`

**Bargaining protocols** → `src/vmt_engine/game_theory/bargaining/`
- How paired agents negotiate prices
- Example: `split_difference.py`, `take_it_or_leave_it.py`

## Effect Types

Return appropriate effects for your protocol:

**Search protocols typically return**:
- `SetTarget(agent_id, target_pos)` - Set movement target
- `ClaimResource(agent_id, pos)` - Claim forage target

**Matching protocols typically return**:
- `Pair(agent_i, agent_j)` - Establish pairing
- `Unpair(agent_i, agent_j, reason)` - Break pairing

**Bargaining protocols typically return**:
- `Trade(agent_i, agent_j, delta_A, delta_B, price)` - Execute trade
- `SetCooldown(agent_id, partner_id, until_tick)` - Set trade cooldown

## Protocol Registration

**Must import in module's `__init__.py` to trigger registration**:

```python
# src/vmt_engine/agent_based/search/__init__.py
from . import legacy
from . import myopic
from . import random_walk  # Your new protocol
```

**Verify registration**:
```python
from vmt_engine.protocols import list_all_protocols
protocols = list_all_protocols()
print(protocols['search'])  # Should include 'my_protocol_name'
```

## WorldView Access Patterns

**Read agent data**:
```python
agent_view = context.world_view.agents[agent_id]
# Access: pos, inventory, quotes, vision_radius, paired_with_id
```

**Query spatial relationships**:
```python
neighbors = context.world_view.spatial_index.query_radius(pos, radius)
```

**Access resources**:
```python
resource_view = context.world_view.resources.get(pos)
# Returns ResourceView or None
```

**Important**: WorldView is immutable. Never call methods that would mutate state.

## Testing Protocols

**Unit test pattern**:
```python
def test_my_protocol():
    # Create mock WorldView
    world_view = create_world_view(agents={...}, resources={...})
    context = create_protocol_context(
        agent_id=1, 
        world_view=world_view,
        tick=0
    )
    
    # Execute protocol
    protocol = MyProtocol()
    effects = protocol.execute(context)
    
    # Assert expected effects
    assert len(effects) == expected_count
    assert isinstance(effects[0], ExpectedEffectType)
```

**Integration test pattern**:
```python
def test_my_protocol_in_simulation():
    # Create scenario with your protocol
    scenario = load_scenario("scenarios/test/my_protocol_test.yaml")
    sim = Simulation(scenario, seed=42)
    sim.run(max_ticks=20)
    
    # Assert expected outcomes
    assert len(sim.telemetry.recent_trades_for_renderer) >= expected_trades
```

## Common Mistakes

1. **Mutating context objects** - WorldView is read-only
2. **Returning mutated state** - Return effects, not modified agents
3. **Forgetting registration** - Protocol won't be available in scenarios
4. **Non-deterministic logic** - Use context.rng for randomness, not global random
5. **Side effects** - No I/O, no logging, no state mutation in execute()

