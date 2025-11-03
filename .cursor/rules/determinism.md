# Determinism Rules

VMT simulations must be **bit-identical** for the same seed. These rules are non-negotiable.

## Required Iteration Patterns

**Always sort agents by ID**:
```python
# CORRECT
for agent in sorted(agents, key=lambda a: a.id):
    process_agent(agent)

# WRONG - undefined order
for agent in agents_dict.values():
    process_agent(agent)
```

**Always sort trade pairs**:
```python
# CORRECT
for i, j in sorted(pairs, key=lambda p: (min(p), max(p))):
    attempt_trade(i, j)

# WRONG
for i, j in pairs:
    attempt_trade(i, j)
```

## Tie-Breaking Rules

**Movement tie-breaking** (in `systems/movement.py`):
- Reduce `|dx|` before `|dy|`
- Prefer negative direction when distances equal
- Diagonal deadlock: only higher ID moves

**Pairing tie-breaking**:
- Lower ID agent executes mutual consent pairing
- Pass 3 greedy matching processes by descending surplus

## Random Number Generation

**Use seeded numpy generators**:
```python
# CORRECT
rng = np.random.Generator(np.random.PCG64(seed))
choice = rng.choice(items)

# WRONG - global random state
import random
choice = random.choice(items)
```

## Quote Stability

**Quotes are frozen during tick**:
- Set `agent.inventory_changed = True` to mark for refresh
- Actual refresh happens only in Housekeeping phase
- Never call `refresh_quotes()` mid-tick

## Integer Math

**Always use round-half-up for trade quantities**:
```python
# CORRECT
delta_B = int(np.floor(price * delta_A + 0.5))

# WRONG - Python's round() uses banker's rounding
delta_B = round(price * delta_A)
```

## Testing Determinism

Every new feature must include determinism test:
```python
def test_my_feature_determinism():
    sim1 = Simulation(scenario, seed=42, log_config=LogConfig.standard())
    sim1.run(max_ticks=20)
    
    sim2 = Simulation(scenario, seed=42, log_config=LogConfig.standard())
    sim2.run(max_ticks=20)
    
    # Compare final states
    for a1, a2 in zip(sim1.agents, sim2.agents):
        assert a1.inventory == a2.inventory
        assert a1.pos == a2.pos
```

## Common Violations to Avoid

1. Using `dict.values()` iteration for side effects
2. Mutating state during iteration without sorting
3. Using global random without seed
4. Refreshing quotes mid-tick
5. Non-deterministic tie-breaking in matching/pairing

