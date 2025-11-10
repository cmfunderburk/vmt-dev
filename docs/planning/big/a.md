# BIG Refactor Plan to De-LLM the Project

Functionally, the current project provides a sound baseline. Structurally, it needs work for extensibility.

Current structure is fragmented:
```
vmt-engine/
├── agent_based/
├── core/
├── econ/
├── game_theory/
├── protocols/
├── systems/
├── simulation.py
```

This is unwieldy. The logical structure should align with:
1. **The launcher** — users choose agent-based, game theory, or neoclassical engine
2. **Economic theory** — agents, space, interaction, outcomes
3. **Code clarity** — single responsibility, clear dependencies

---

## Three Options to Consider

### Option A: Component-Oriented
```
vmt-engine/
├── agent/          (BaseAgent + utilities)
├── spatial/        (grid, indexing, movement)
├── interaction/    (search, matching, bargaining protocols)
├── protocol/       (protocol orchestration)
├── simulation/     (simulation engine)
└── core/           (just decimal_config)
```
**Pros**: Clean layering, domain-aligned, clear where to add things  
**Cons**: More files to reorganize

### Option B: Engines-First
```
vmt-engine/
├── engines/
│   ├── agent_based_engine.py
│   ├── game_theory_engine.py
│   └── neoclassical_engine.py
├── shared/         (agent, spatial, protocols, etc.)
```
**Pros**: Explicit entry points, future-proofs for multiple engines  
**Cons**: Shared/ still needs internal structure

### Option C: Minimal Consolidation
```
vmt-engine/
├── agent/          (core/agent.py + econ/utility.py)
├── space/          (core/grid.py, spatial_index.py)
├── protocols/      (merge game_theory/ into here)
├── systems/        (systems/ as-is, just organized)
└── simulation.py
```
**Pros**: Fewest file moves, quickest  
**Cons**: Less thorough restructuring

---

## Key Questions

1. **How coupled should protocols be?** Are search+matching+bargaining always used together, or can they be mixed independently?

2. **Where do movement & trade helpers belong?** Currently scattered in systems/; should they move to protocols/ or domain layers?

3. **How much refactoring bandwidth do we have?** (Quick vs. thorough trade-off)

Which option resonates? Or do you want to hybridize?
