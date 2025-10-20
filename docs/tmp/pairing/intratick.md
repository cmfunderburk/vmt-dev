Perfect. Now let me design the **two-pass mutual consent algorithm** for the DecisionSystem.

---

## Two-Pass Mutual Consent Algorithm

### Architecture Overview

```
Pass 1: Target Selection (agent ID order)
├─ Paired agents: Validate pairing, maintain target lock
└─ Unpaired agents: Evaluate neighbors, choose best partner candidate

Pass 2: Pairing Establishment (agent ID order)  
├─ Check for mutual consent between unpaired agents
├─ Establish bidirectional pairings when mutual
└─ Log all decisions with final pairing status
```

**Key invariants:**
1. Pass 1 operates on agent state from end of previous tick
2. Pass 2 reads `target_agent_id` set during Pass 1 of *current* tick
3. Only Pass 2 modifies `paired_with_id`
4. All operations maintain agent ID order for determinism

---

## Detailed Implementation Design

### Pass 1: Target Selection

**Purpose:** Each agent independently chooses their preferred action/partner based on current perception

**For paired agents:**
```python
# Validate existing pairing
if agent.paired_with_id is not None:
    partner = sim.agent_by_id.get(agent.paired_with_id)
    
    if partner is None or partner.paired_with_id != agent.id:
        # Pairing corrupted, clear and fall through to unpaired logic
        agent.paired_with_id = None
    else:
        # Valid pairing: maintain target lock
        agent.target_pos = partner.pos
        agent.target_agent_id = partner.id
        continue  # Skip to next agent
```

**For unpaired agents (trade mode):**
```python
# Evaluate neighbors using existing choose_partner logic
neighbors = view.get("neighbors", [])
partner_id, surplus, candidates = self._choose_trade_target(agent, view, sim)

if partner_id is not None:
    # Set target (does NOT establish pairing yet)
    partner = sim.agent_by_id[partner_id]
    agent.target_pos = partner.pos
    agent.target_agent_id = partner_id
    # Store surplus for logging (temporary)
    agent._decision_surplus = surplus
    agent._decision_candidates = candidates
else:
    # No suitable partner
    agent.target_pos = None
    agent.target_agent_id = None
    agent._decision_surplus = None
    agent._decision_candidates = []
```

**For unpaired agents (mixed mode):**
```python
# Try trade first, fall back to forage
partner_id, surplus, candidates = self._choose_trade_target(agent, view, sim)

if partner_id is not None:
    partner = sim.agent_by_id[partner_id]
    agent.target_pos = partner.pos
    agent.target_agent_id = partner_id
    agent._decision_surplus = surplus
    agent._decision_candidates = candidates
else:
    # Fall back to foraging
    target_pos, target_type = self._choose_forage_target(agent, view, sim)
    agent.target_pos = target_pos
    agent.target_agent_id = None
    agent._decision_surplus = None
    agent._decision_candidates = candidates
    agent._decision_target_type = target_type
```

---

### Pass 2: Pairing Establishment & Logging

**Purpose:** Detect mutual consent and establish pairings using fresh `target_agent_id` data from Pass 1

```python
for agent in sorted(sim.agents, key=lambda a: a.id):
    view = agent.perception_cache
    
    # Case 1: Already paired (validated in Pass 1)
    if agent.paired_with_id is not None:
        self._log_decision(
            sim, agent, agent.paired_with_id, None, "trade_paired",
            agent.target_pos, view, []
        )
        continue
    
    # Case 2: Agent wants to trade
    if agent.target_agent_id is not None:
        partner_id = agent.target_agent_id
        partner = sim.agent_by_id[partner_id]
        
        # Check mutual consent using CURRENT TICK data
        if partner.target_agent_id == agent.id and partner.paired_with_id is None:
            # MUTUAL CONSENT DETECTED
            # Only establish pairing if agent.id < partner_id (process once)
            if agent.id < partner_id:
                agent.paired_with_id = partner_id
                partner.paired_with_id = agent.id
                
                # Clear cooldowns
                agent.trade_cooldowns.pop(partner_id, None)
                partner.trade_cooldowns.pop(agent.id, None)
                
                # Log pairing event
                sim.telemetry.log_pairing_event(
                    sim.tick, agent.id, partner_id, "pair", "mutual_consent"
                )
            
            # Both agents log as newly paired
            self._log_decision(
                sim, agent, partner_id, agent._decision_surplus, 
                "trade_new_pair", agent.target_pos, view, 
                agent._decision_candidates
            )
        else:
            # Seeking trade but no mutual consent
            self._log_decision(
                sim, agent, partner_id, agent._decision_surplus,
                "trade", agent.target_pos, view,
                agent._decision_candidates
            )
    
    # Case 3: Foraging or idle
    else:
        target_type = getattr(agent, '_decision_target_type', 'idle')
        self._log_decision(
            sim, agent, None, None, target_type,
            agent.target_pos, view, agent._decision_candidates
        )
```

---

## Critical Edge Cases

### Edge Case 1: Three-way mutual preference
```
Agent A wants B (surplus 0.8)
Agent B wants C (surplus 1.0)  
Agent C wants A (surplus 0.9)
```

**Resolution:** No pairings established (mutual consent requires bidirectional preference)

### Edge Case 2: Bidirectional preference with existing pairing
```
Agent A (paired with C) wants C
Agent B (unpaired) wants A
Agent C (paired with A) wants A
```

**Resolution:** A-C remain paired, B stays unpaired

### Edge Case 3: Cooldown expires same tick as mutual consent
```
Tick 50: A and B have cooldown until tick 51
Tick 51: Both choose each other
```

**Resolution:** `choose_partner` removes expired cooldown in Pass 1, pairing establishes in Pass 2 ✓

---

## Additional Data Fields Needed

Since we're using temporary fields to carry data between passes, we should be explicit:

**Option A: Use temporary attributes (lightweight)**
```python
# Set in Pass 1, read in Pass 2, no cleanup needed
agent._decision_surplus = surplus
agent._decision_candidates = candidates
agent._decision_target_type = target_type
```

**Option B: Use a decision context dict (cleaner)**
```python
# In DecisionSystem.__init__
self._decision_contexts: dict[int, dict] = {}

# Pass 1: Store
self._decision_contexts[agent.id] = {
    'surplus': surplus,
    'candidates': candidates,
    'target_type': target_type
}

# Pass 2: Retrieve
ctx = self._decision_contexts.get(agent.id, {})
```

**Recommendation:** Option A for simplicity - the underscore prefix signals temporary/internal use.

---

## Performance Impact

**Current (single-pass):** O(N) iteration  
**Proposed (two-pass):** O(2N) = O(N) iteration  

**No algorithmic complexity change**, just 2× constant factor. The pairing performance benefit (O(N²) → O(N) in trade phase) vastly outweighs this.

---

## Questions for You

1. **Temporary data storage:** Option A (agent attributes) or Option B (context dict)?

2. **Pairing symmetry in logging:** Should both agents log "trade_new_pair" when they pair, or only the lower-ID agent? (Current design: both log it)

3. **Pass 1 validation timing:** Should pairing corruption cleanup happen in Pass 1 or leave it to Housekeeping? (Current design: Pass 1 cleans up immediately)

4. **Mode forage handling:** In Pass 1 mixed mode, should we evaluate trade opportunities for currently-paired agents, or immediately skip to maintaining their pairing? (Affects whether paired agents can notice better partners)

Let me know your preferences and I'll refine the implementation specification for the actual code changes.