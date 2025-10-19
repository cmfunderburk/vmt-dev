### Money Implementation — Phase 5: Liquidity Gating

Author: VMT Assistant
Date: 2025-10-19

**Prerequisite**: Phase 4 complete (mixed regime working)

**Goal**: Implement `mixed_liquidity_gated` regime where barter is conditionally enabled based on perceived money market depth.

**Success Criteria**:
- Liquidity depth metric implemented deterministically
- Barter enabled/disabled per agent based on money market depth
- Agents fall back to barter when money markets thin
- Heterogeneous money holdings create interesting dynamics

---

## Pre-Phase 5 Verification

- [ ] **Verify Phase 4 complete**
  ```bash
  pytest tests/test_mixed_regime*.py -v
  python main.py scenarios/money_test_mixed.yaml --seed 42
  # Verify mixed trades work
  ```

- [ ] **Create Phase 5 branch**
  ```bash
  git checkout -b feature/money-phase5-liquidity-gating
  ```

- [ ] **Create liquidity gating test scenarios**
  ```bash
  # Create scenarios/money_test_liquidity_gate.yaml
  # Create scenarios/money_test_sparse_liquidity.yaml
  ```

---

## Part 1: Test Scenario Creation

### 1.1) Create liquidity gating scenario

**File**: `scenarios/money_test_liquidity_gate.yaml` (create new)

- [ ] **Write scenario with heterogeneous money holdings**
  ```yaml
  schema_version: 1
  name: "Liquidity Gating Test"
  N: 20
  agents: 12
  
  # Heterogeneous money holdings: some agents have money, some don't
  initial_inventories:
    A: [10, 8, 6, 4, 2, 0, 5, 7, 3, 9, 1, 6]
    B: [0, 2, 4, 6, 8, 10, 5, 3, 7, 1, 9, 4]
    M: [100, 100, 100, 100, 0, 0, 0, 50, 50, 150, 0, 0]
        # First 4 agents: wealthy
        # Agents 4-6, 10-11: no money (must barter)
        # Agents 7-9: some money
  
  utilities:
    mix:
      - type: ces
        weight: 1.0
        params:
          rho: 0.4
          wA: 0.6
          wB: 0.4
  
  params:
    spread: 0.1
    vision_radius: 10
    interaction_radius: 1
    move_budget_per_tick: 2
    dA_max: 3
    forage_rate: 1
    
    # Liquidity gated regime
    exchange_regime: mixed_liquidity_gated
    money_mode: quasilinear
    money_scale: 1
    lambda_money: 1.0
    liquidity_gate:
      min_quotes: 3  # Need 3+ distinct neighbor money quotes to avoid barter
  
  resource_seed:
    density: 0.2
    amount: 4
  ```

### 1.2) Create sparse liquidity scenario

**File**: `scenarios/money_test_sparse_liquidity.yaml` (create new)

- [ ] **Write scenario where agents are spread out**
  ```yaml
  schema_version: 1
  name: "Sparse Liquidity (Forces Barter)"
  N: 30
  agents: 8  # Few agents on large grid
  
  initial_inventories:
    A: [10, 5, 8, 3, 6, 4, 7, 9]
    B: [0, 5, 2, 7, 4, 6, 3, 1]
    M: [100, 100, 100, 100, 100, 100, 100, 100]  # All have money
  
  utilities:
    mix:
      - type: ces
        weight: 1.0
        params:
          rho: 0.5
          wA: 0.5
          wB: 0.5
  
  params:
    spread: 0.1
    vision_radius: 5  # Small vision radius
    interaction_radius: 1
    move_budget_per_tick: 1
    dA_max: 3
    forage_rate: 1
    
    # Liquidity gated with sparse agents
    exchange_regime: mixed_liquidity_gated
    money_mode: quasilinear
    money_scale: 1
    lambda_money: 1.0
    liquidity_gate:
      min_quotes: 2  # Low threshold
  
  resource_seed:
    density: 0.1
    amount: 3
  ```

---

## Part 2: Liquidity Depth Metric Implementation

### 2.1) Implement depth measurement

**File**: `src/vmt_engine/systems/trading.py` (or new `liquidity.py` module)

- [ ] **Add `_compute_liquidity_depth()` function**
  ```python
  def _compute_liquidity_depth(agent: Agent, neighbors: list[Agent], 
                                epsilon: float) -> dict[str, int]:
      """
      Compute perceived liquidity depth for each good.
      
      Depth = count of distinct neighbor money quotes.
      
      Args:
          agent: Agent measuring depth
          neighbors: Neighbors within vision_radius
          epsilon: Small constant
          
      Returns:
          dict with keys 'A', 'B' mapping to depth counts
      """
      # Collect unique sellers offering each good for money
      sellers_A = set()
      sellers_B = set()
      
      # Include self if has money quotes
      if 'ask_A_in_M' in agent.quotes and agent.quotes['ask_A_in_M'] > epsilon:
          sellers_A.add(agent.id)
      if 'ask_B_in_M' in agent.quotes and agent.quotes['ask_B_in_M'] > epsilon:
          sellers_B.add(agent.id)
      
      # Collect from neighbors (sorted by ID for determinism)
      for neighbor in sorted(neighbors, key=lambda n: n.id):
          if 'ask_A_in_M' in neighbor.quotes and neighbor.quotes['ask_A_in_M'] > epsilon:
              sellers_A.add(neighbor.id)
          if 'ask_B_in_M' in neighbor.quotes and neighbor.quotes['ask_B_in_M'] > epsilon:
              sellers_B.add(neighbor.id)
      
      return {
          'A': len(sellers_A),
          'B': len(sellers_B)
      }
  ```

- [ ] **Test depth computation**
  ```python
  # In tests/test_liquidity_depth.py (create new)
  def test_depth_includes_self():
      """Verify agent includes self in depth count."""
      # Create agent with ask_A_in_M
      # Call _compute_liquidity_depth with empty neighbors
      # Verify: depth['A'] == 1
      pass
  
  def test_depth_deduplication():
      """Verify depth counts unique sellers only."""
      # Create 3 neighbors, all with ask_A_in_M
      # Verify: depth['A'] == 3 (not 3 × number of quotes)
      pass
  
  def test_depth_deterministic():
      """Verify depth computation is deterministic."""
      # Same neighbors in different order
      # Verify: same depth result
      pass
  ```

### 2.2) Integrate depth check into pair enumeration

**File**: `src/vmt_engine/systems/trading.py`

- [ ] **Add `_get_allowed_pairs_with_gating()` method**
  ```python
  def _get_allowed_pairs_with_gating(self, agent: Agent, sim: "Simulation") -> list[tuple[str, str]]:
      """
      Get allowed pairs for agent, accounting for liquidity gating.
      
      For mixed_liquidity_gated regime:
      - Always allow money pairs (A↔M, B↔M)
      - Allow barter pairs (A↔B) only if liquidity depth < threshold
      """
      regime = sim.params['exchange_regime']
      
      if regime != "mixed_liquidity_gated":
          # Use standard logic
          return self._get_allowed_pairs(regime)
      
      # Compute liquidity depth
      neighbor_ids = sim.spatial_index.query_radius(agent.pos, agent.vision_radius)
      neighbors = [sim.agent_by_id[nid] for nid in neighbor_ids if nid != agent.id]
      
      depth = _compute_liquidity_depth(agent, neighbors, sim.params['epsilon'])
      
      threshold = sim.params['liquidity_gate']['min_quotes']
      
      # Always allow money pairs
      allowed = [("A", "M"), ("B", "M")]
      
      # Conditionally allow barter
      # If either good has insufficient liquidity, enable barter
      if depth['A'] < threshold or depth['B'] < threshold:
          allowed.extend([("A", "B"), ("B", "A")])
      
      return allowed
  ```

- [ ] **Update TradeSystem.execute() to use per-agent gating**
  ```python
  class TradeSystem:
      def execute(self, sim: "Simulation") -> None:
          # ... existing checks ...
          
          regime = sim.params['exchange_regime']
          
          candidates = []
          
          for buyer in sim.agents:
              # Get allowed pairs for THIS agent (may differ per agent in gated regime)
              if regime == "mixed_liquidity_gated":
                  allowed_pairs = self._get_allowed_pairs_with_gating(buyer, sim)
              else:
                  allowed_pairs = self._get_allowed_pairs(regime)
              
              # ... rest of matching logic using allowed_pairs ...
  ```

---

## Part 3: Telemetry and Diagnostics

### 3.1) Log liquidity depth per agent

**File**: `src/telemetry/db_loggers.py`

- [ ] **Extend agent snapshots to include depth**
  ```python
  # Add columns to agent_snapshots (if not already in schema):
  # liquidity_depth_A INTEGER DEFAULT NULL
  # liquidity_depth_B INTEGER DEFAULT NULL
  # barter_enabled INTEGER DEFAULT NULL
  
  # In log_agent_snapshot(), optionally log depth if in gated regime
  ```

- [ ] **Add depth to snapshot logging**
  ```python
  # In simulation or trading system:
  if sim.params['exchange_regime'] == 'mixed_liquidity_gated':
      # Compute and store depth on agent for logging
      agent._liquidity_depth = _compute_liquidity_depth(agent, neighbors, epsilon)
      agent._barter_enabled = (depth['A'] < threshold or depth['B'] < threshold)
  ```

### 3.2) Create liquidity analysis script

**File**: `scripts/analyze_liquidity_dynamics.py` (create new)

- [ ] **Script to analyze depth over time**
  ```python
  import sqlite3
  import matplotlib.pyplot as plt
  
  def analyze_liquidity_dynamics(db_path: str, run_id: int, agent_id: int):
      """Analyze liquidity depth and barter usage for an agent."""
      conn = sqlite3.connect(db_path)
      
      # Query depth over time
      cursor = conn.execute("""
          SELECT tick, liquidity_depth_A, liquidity_depth_B 
          FROM agent_snapshots 
          WHERE run_id=? AND agent_id=?
          ORDER BY tick
      """, (run_id, agent_id))
      
      data = list(cursor)
      
      # Query trades by type
      cursor = conn.execute("""
          SELECT tick, exchange_pair_type 
          FROM trades 
          WHERE run_id=? AND (buyer_id=? OR seller_id=?)
          ORDER BY tick
      """, (run_id, agent_id, agent_id))
      
      trades = list(cursor)
      conn.close()
      
      # Plot
      if data:
          ticks = [row[0] for row in data]
          depth_A = [row[1] for row in data]
          depth_B = [row[2] for row in data]
          
          plt.figure(figsize=(12, 4))
          plt.subplot(1, 2, 1)
          plt.plot(ticks, depth_A, label='Depth A')
          plt.plot(ticks, depth_B, label='Depth B')
          plt.axhline(y=3, color='r', linestyle='--', label='Threshold')
          plt.xlabel('Tick')
          plt.ylabel('Liquidity Depth')
          plt.title(f'Agent {agent_id}: Perceived Liquidity')
          plt.legend()
          plt.grid(True)
          
          plt.subplot(1, 2, 2)
          # Plot trade types
          trade_ticks = [t[0] for t in trades]
          trade_types = [t[1] for t in trades]
          
          for i, (tick, ttype) in enumerate(zip(trade_ticks, trade_types)):
              color = 'gold' if 'M' in ttype else 'green'
              plt.scatter(tick, i, c=color, s=50)
          
          plt.xlabel('Tick')
          plt.ylabel('Trade Event')
          plt.title(f'Agent {agent_id}: Trade Types (gold=money, green=barter)')
          plt.grid(True)
          
          plt.tight_layout()
          plt.show()
  
  if __name__ == '__main__':
      import sys
      analyze_liquidity_dynamics(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
  ```

---

## Part 4: Testing

### 4.1) Unit tests

**File**: `tests/test_liquidity_gating.py` (create new)

- [ ] **Test depth threshold logic**
  ```python
  def test_barter_enabled_below_threshold():
      """Verify barter enabled when depth < threshold."""
      threshold = 3
      depth = {'A': 2, 'B': 5}
      
      # Depth['A'] < threshold, so barter should be enabled
      barter_enabled = (depth['A'] < threshold or depth['B'] < threshold)
      assert barter_enabled
  
  def test_barter_disabled_above_threshold():
      """Verify barter disabled when depth >= threshold."""
      threshold = 3
      depth = {'A': 4, 'B': 5}
      
      barter_enabled = (depth['A'] < threshold or depth['B'] < threshold)
      assert not barter_enabled
  ```

- [ ] **Test per-agent gating**
  ```python
  def test_different_agents_different_pairs():
      """Verify agents in different liquidity environments get different pairs."""
      # Agent 0: surrounded by money traders -> depth high -> no barter
      # Agent 1: isolated -> depth low -> barter enabled
      # Verify: allowed_pairs differ per agent
      pass
  ```

### 4.2) Integration tests

**File**: `tests/test_liquidity_gating_integration.py` (create new)

- [ ] **Test liquidity gated scenario**
  ```python
  def test_liquidity_gated_scenario():
      """Run liquidity_gate scenario and verify barter fallback."""
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      import sqlite3
      import tempfile
      
      with tempfile.TemporaryDirectory() as tmpdir:
          db_path = f"{tmpdir}/test.db"
          config = load_scenario("scenarios/money_test_liquidity_gate.yaml")
          log_cfg = LogConfig(use_database=True, db_path=db_path)
          
          sim = Simulation(config, seed=42, log_config=log_cfg)
          sim.run(max_ticks=100)
          sim.close()
          
          # Query trades by agents with no money
          conn = sqlite3.connect(db_path)
          
          # Agents 4, 5, 6 have M=0 (should primarily barter)
          cursor = conn.execute("""
              SELECT exchange_pair_type, COUNT(*) 
              FROM trades 
              WHERE run_id=1 AND (buyer_id IN (4,5,6) OR seller_id IN (4,5,6))
              GROUP BY exchange_pair_type
          """)
          
          pair_counts = dict(cursor.fetchall())
          conn.close()
          
          # Expect barter trades for agents without money
          barter_count = sum(v for k, v in pair_counts.items() if 'M' not in k)
          
          # Should have at least some barter trades
          assert barter_count > 0
  ```

- [ ] **Test sparse liquidity scenario**
  ```python
  def test_sparse_liquidity_forces_barter():
      """Verify sparse agents fall back to barter despite having money."""
      # Load sparse scenario
      # Run simulation
      # Query trades
      # Even though agents have M, if spread out, should see barter
      pass
  ```

### 4.3) Comparative test

- [ ] **Compare gated vs. ungated**
  ```python
  def test_compare_gated_vs_ungated():
      """Compare outcomes between mixed and mixed_liquidity_gated."""
      # Same initial conditions
      # Run with mixed regime
      # Run with mixed_liquidity_gated regime
      # Compare trade type distributions
      # Document findings
      pass
  ```

---

## Part 5: Pedagogical Scenarios

### 5.1) Create "emergence of barter" scenario

**File**: `scenarios/money_emergence_of_barter.yaml` (create new)

- [ ] **Design scenario showing barter emergence in thin markets**
  ```yaml
  # Scenario where:
  # - Initial: agents clustered, plenty of money quotes
  # - Movement disperses agents
  # - As liquidity thins, barter emerges
  # Good for teaching!
  ```

### 5.2) Create "liquidity zones" scenario

**File**: `scenarios/money_liquidity_zones.yaml` (create new)

- [ ] **Design scenario with spatial heterogeneity**
  ```yaml
  # Place money-rich agents in one region
  # Place money-poor agents in another
  # Observe different exchange types by region
  ```

---

## Part 6: Documentation

### 6.1) Document liquidity gating

- [ ] **Add section to README**
  - Explain `mixed_liquidity_gated` regime
  - When to use it (modeling thin vs. thick markets)
  - Pedagogical value (emergence of money vs. barter)

- [ ] **Document depth metric**
  - Explain count-of-distinct-quotes approach
  - Rationale for including self
  - Determinism guarantees

### 6.2) Create teaching guide

**File**: `docs/teaching_liquidity_gating.md` (create new)

- [ ] **Write teaching guide**
  - Historical context (when did money emerge?)
  - Model interpretation (what is "liquidity depth"?)
  - Classroom exercises using VMT scenarios
  - Discussion questions

---

## Completion Criteria

**Phase 5 is complete when**:

✅ Liquidity depth metric implemented deterministically
✅ `mixed_liquidity_gated` regime enables/disables barter per agent
✅ Heterogeneous money scenarios demonstrate fallback to barter
✅ Sparse liquidity scenario shows barter emergence despite money availability
✅ Telemetry logs depth and barter-enabled status
✅ Analysis scripts visualize liquidity dynamics
✅ All Phase 4 tests still pass
✅ Teaching guide written

**Ready for Phase 6 when**:
- Can demonstrate barter emergence in thin markets
- Can show spatial heterogeneity in exchange types
- Liquidity depth correlates with trade type in logs
- Pedagogical scenarios work well for teaching

---

**Estimated effort**: 8-10 hours

See also:
- `money_SSOT_implementation_plan.md` §7.1, §8.1
- `money_phase4_checklist.md` (prerequisite)
- `money_telemetry_schema.md` (agent snapshot extensions)

