### Money Implementation — Phase 3: KKT λ Estimation

Author: VMT Assistant
Date: 2025-10-19

**Prerequisite**: Phase 2 complete (quasi-linear money trades working)

**Goal**: Implement KKT λ estimation mode where agents endogenously estimate marginal utility of money from observed prices.

**Success Criteria**:
- λ updates based on neighbor price aggregation
- Median-lower aggregation deterministic and stable
- λ converges within bounds
- Smoothing parameter (alpha) works correctly
- No O(N²) performance paths

---

## Pre-Phase 3 Verification

- [ ] **Verify Phase 2 complete**
  ```bash
  pytest tests/test_money_phase2.py -v
  python main.py scenarios/money_test_basic.yaml --seed 42
  # Verify money trades occur
  ```

- [ ] **Create Phase 3 branch**
  ```bash
  git checkout -b feature/money-phase3-kkt-lambda
  ```

- [ ] **Create KKT test scenario**
  ```bash
  # Create scenarios/money_test_kkt.yaml (see Part 1.1)
  ```

---

## Part 1: Test Scenario Creation

### 1.1) Create KKT test scenario

**File**: `scenarios/money_test_kkt.yaml` (create new)

- [ ] **Write KKT scenario**
  ```yaml
  schema_version: 1
  name: "KKT Lambda Estimation Test"
  N: 15
  agents: 10
  
  initial_inventories:
    A: [10, 8, 6, 4, 2, 0, 0, 2, 4, 6]
    B: [0, 2, 4, 6, 8, 10, 8, 6, 4, 2]
    M: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
  
  utilities:
    mix:
      - type: ces
        weight: 0.7
        params:
          rho: 0.5
          wA: 0.6
          wB: 0.4
      - type: ces
        weight: 0.3
        params:
          rho: -0.5
          wA: 0.5
          wB: 0.5
  
  params:
    spread: 0.05
    vision_radius: 8
    interaction_radius: 1
    move_budget_per_tick: 1
    dA_max: 3
    forage_rate: 1
    
    # KKT mode params
    exchange_regime: money_only
    money_mode: kkt_lambda
    money_scale: 1
    lambda_money: 1.0           # Initial λ
    lambda_update_rate: 0.2     # Smoothing alpha
    lambda_bounds:
      lambda_min: 0.000001
      lambda_max: 1000000.0
  
  resource_seed:
    density: 0.15
    amount: 5
  ```

- [ ] **Verify scenario loads**
  ```bash
  python -c "from scenarios.loader import load_scenario; cfg = load_scenario('scenarios/money_test_kkt.yaml'); print(f'KKT mode: {cfg.params.money_mode}')"
  ```

---

## Part 2: Price Aggregation System

### 2.1) Implement neighbor price collection

**File**: `src/vmt_engine/systems/housekeeping.py`

- [ ] **Add `_collect_neighbor_prices()` helper**
  ```python
  def _collect_neighbor_prices(agent: Agent, neighbors: list[Agent], 
                                good: str, epsilon: float) -> list[tuple[float, int]]:
      """
      Collect neighbor ask prices for a good in money.
      
      Args:
          agent: Agent collecting prices
          neighbors: List of neighbors within vision_radius
          good: "A" or "B"
          epsilon: Small constant for safety
          
      Returns:
          List of (price, seller_id) tuples, sorted for determinism
      """
      prices = []
      
      # Include self price
      if good == "A" and 'ask_A_in_M' in agent.quotes:
          prices.append((agent.quotes['ask_A_in_M'], agent.id))
      elif good == "B" and 'ask_B_in_M' in agent.quotes:
          prices.append((agent.quotes['ask_B_in_M'], agent.id))
      
      # Collect neighbor prices
      for neighbor in neighbors:
          if good == "A" and 'ask_A_in_M' in neighbor.quotes:
              prices.append((neighbor.quotes['ask_A_in_M'], neighbor.id))
          elif good == "B" and 'ask_B_in_M' in neighbor.quotes:
              prices.append((neighbor.quotes['ask_B_in_M'], neighbor.id))
      
      # Sort deterministically: (price, seller_id)
      prices.sort(key=lambda x: (x[0], x[1]))
      
      return prices
  ```

### 2.2) Implement median-lower aggregation

- [ ] **Add `_aggregate_prices_median_lower()` helper**
  ```python
  def _aggregate_prices_median_lower(prices: list[tuple[float, int]]) -> float | None:
      """
      Aggregate prices using median-lower rule.
      
      For even-length lists, take the lower of the two middle values.
      For odd-length lists, take the exact median.
      
      Args:
          prices: Sorted list of (price, seller_id) tuples
          
      Returns:
          Aggregated price, or None if prices is empty
      """
      if not prices:
          return None
      
      n = len(prices)
      if n % 2 == 1:
          # Odd: take exact median
          return prices[n // 2][0]
      else:
          # Even: take lower of two middle values
          return prices[(n // 2) - 1][0]
  ```

- [ ] **Test price aggregation**
  ```python
  # In tests/test_kkt_price_aggregation.py (create new)
  def test_median_lower_odd():
      prices = [(1.0, 0), (2.0, 1), (3.0, 2)]
      result = _aggregate_prices_median_lower(prices)
      assert result == 2.0
  
  def test_median_lower_even():
      prices = [(1.0, 0), (2.0, 1), (3.0, 2), (4.0, 3)]
      result = _aggregate_prices_median_lower(prices)
      assert result == 2.0  # Lower of [2.0, 3.0]
  
  def test_median_lower_deterministic():
      # Same prices, different seller IDs
      prices1 = [(2.0, 0), (2.0, 1), (2.0, 2)]
      prices2 = [(2.0, 2), (2.0, 1), (2.0, 0)]
      # After sorting by (price, id):
      prices2.sort(key=lambda x: (x[0], x[1]))
      
      r1 = _aggregate_prices_median_lower(prices1)
      r2 = _aggregate_prices_median_lower(prices2)
      assert r1 == r2
  ```

### 2.3) Implement cross-quote inference fallback

- [ ] **Add `_infer_price_from_cross_quotes()` helper**
  ```python
  def _infer_price_from_cross_quotes(agent: Agent, good: str, 
                                      p_other: float | None, 
                                      neighbors: list[Agent],
                                      epsilon: float) -> float | None:
      """
      Infer price of good A (or B) from prices of B (or A) using cross quotes.
      
      If no direct A-in-M quotes are available, but B-in-M quotes are,
      use p_A ≈ p_B * (B_in_A cross quote).
      
      Args:
          agent: Agent inferring price
          good: "A" or "B"
          p_other: Aggregated price of the other good (can be None)
          neighbors: Neighbors for collecting cross quotes
          epsilon: Small constant
          
      Returns:
          Inferred price or None
      """
      if p_other is None:
          return None
      
      # Collect cross quotes (A<->B)
      if good == "A":
          # Need p_B and bid_A_in_B (how much B per A)
          # p_A ≈ p_B / bid_A_in_B
          if 'bid_A_in_B' in agent.quotes:
              return p_other / max(agent.quotes['bid_A_in_B'], epsilon)
      else:
          # Need p_A and bid_B_in_A
          if 'bid_B_in_A' in agent.quotes:
              return p_other / max(agent.quotes['bid_B_in_A'], epsilon)
      
      return None
  ```

---

## Part 3: λ Update Logic

### 3.1) Implement λ estimation in HousekeepingSystem

**File**: `src/vmt_engine/systems/housekeeping.py`

- [ ] **Add `_update_lambda_kkt()` method to HousekeepingSystem**
  ```python
  def _update_lambda_kkt(self, agent: Agent, sim: "Simulation") -> None:
      """
      Update agent's lambda using KKT estimation.
      
      Steps:
      1. Collect neighbor prices for A and B in money
      2. Aggregate using median-lower
      3. Compute λ_hat_A = MU_A / p_A, λ_hat_B = MU_B / p_B
      4. Set λ_hat = min(λ_hat_A, λ_hat_B)
      5. Smooth: λ_new = (1-α)*λ_old + α*λ_hat
      6. Clamp to bounds
      """
      epsilon = sim.params['epsilon']
      alpha = sim.params['lambda_update_rate']
      bounds = sim.params['lambda_bounds']
      lambda_min = bounds['lambda_min']
      lambda_max = bounds['lambda_max']
      
      # Get neighbors within vision radius
      neighbor_ids = sim.spatial_index.query_radius(agent.pos, agent.vision_radius)
      neighbors = [sim.agent_by_id[nid] for nid in neighbor_ids if nid != agent.id]
      
      # Collect and aggregate prices
      prices_A = self._collect_neighbor_prices(agent, neighbors, "A", epsilon)
      prices_B = self._collect_neighbor_prices(agent, neighbors, "B", epsilon)
      
      p_hat_A = self._aggregate_prices_median_lower(prices_A)
      p_hat_B = self._aggregate_prices_median_lower(prices_B)
      
      # Fallback: infer missing prices from cross quotes
      if p_hat_A is None and p_hat_B is not None:
          p_hat_A = self._infer_price_from_cross_quotes(agent, "A", p_hat_B, neighbors, epsilon)
      if p_hat_B is None and p_hat_A is not None:
          p_hat_B = self._infer_price_from_cross_quotes(agent, "B", p_hat_A, neighbors, epsilon)
      
      # If still no prices, keep current λ
      if p_hat_A is None and p_hat_B is None:
          return
      
      # Compute marginal utilities
      mu_A = agent.utility.mu_A(agent.inventory.A, agent.inventory.B, epsilon)
      mu_B = agent.utility.mu_B(agent.inventory.A, agent.inventory.B, epsilon)
      
      # Compute λ estimates
      lambda_hat_A = mu_A / max(p_hat_A, epsilon) if p_hat_A is not None else None
      lambda_hat_B = mu_B / max(p_hat_B, epsilon) if p_hat_B is not None else None
      
      # Take minimum (most binding constraint)
      if lambda_hat_A is not None and lambda_hat_B is not None:
          lambda_hat = min(lambda_hat_A, lambda_hat_B)
      elif lambda_hat_A is not None:
          lambda_hat = lambda_hat_A
      else:
          lambda_hat = lambda_hat_B
      
      # Smooth
      lambda_old = agent.lambda_money
      lambda_new = (1 - alpha) * lambda_old + alpha * lambda_hat
      
      # Clamp to bounds
      clamped = False
      clamp_type = None
      if lambda_new < lambda_min:
          lambda_new = lambda_min
          clamped = True
          clamp_type = "lower"
      elif lambda_new > lambda_max:
          lambda_new = lambda_max
          clamped = True
          clamp_type = "upper"
      
      # Update agent
      agent.lambda_money = lambda_new
      
      # Set flag if change is significant
      tolerance = 1e-9
      if abs(lambda_new - lambda_old) > tolerance:
          agent.lambda_changed = True
      
      # Log lambda update for diagnostics
      if sim.telemetry and abs(lambda_new - lambda_old) > tolerance:
          sim.telemetry.log_lambda_update(
              tick=sim.tick,
              agent_id=agent.id,
              lambda_old=lambda_old,
              lambda_new=lambda_new,
              lambda_hat_A=lambda_hat_A if lambda_hat_A else 0.0,
              lambda_hat_B=lambda_hat_B if lambda_hat_B else 0.0,
              lambda_hat=lambda_hat,
              clamped=clamped,
              clamp_type=clamp_type
          )
  ```

### 3.2) Integrate λ updates into HousekeepingSystem

- [ ] **Call `_update_lambda_kkt()` in `execute()`**
  ```python
  class HousekeepingSystem:
      def execute(self, sim: "Simulation") -> None:
          for agent in sorted(sim.agents, key=lambda a: a.id):
              # Existing: update quotes if inventory changed
              if agent.inventory_changed:
                  agent.quotes = compute_quotes(agent, sim.params['spread'], sim.params['epsilon'])
                  agent.inventory_changed = False
              
              # NEW: update lambda in KKT mode
              if sim.params['money_mode'] == 'kkt_lambda':
                  self._update_lambda_kkt(agent, sim)
                  
                  # If lambda changed, recompute quotes
                  if agent.lambda_changed:
                      agent.quotes = compute_quotes(agent, sim.params['spread'], sim.params['epsilon'])
                      agent.lambda_changed = False
              
              # Existing: cooldown management, etc.
              # ...
  ```

---

## Part 4: Telemetry Integration

### 4.1) Implement `log_lambda_update()`

**File**: `src/telemetry/db_loggers.py`

- [ ] **Complete `log_lambda_update()` implementation**
  ```python
  def log_lambda_update(self, tick: int, agent_id: int,
                       lambda_old: float, lambda_new: float,
                       lambda_hat_A: float, lambda_hat_B: float, 
                       lambda_hat: float,
                       clamped: bool, clamp_type: str = None):
      """Log KKT lambda update."""
      if not self.config.use_database or self.db is None:
          return
      
      self.db.execute("""
          INSERT INTO lambda_updates 
          (run_id, tick, agent_id, lambda_old, lambda_new,
           lambda_hat_A, lambda_hat_B, lambda_hat, clamped, clamp_type)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (self.run_id, tick, agent_id, lambda_old, lambda_new,
            lambda_hat_A, lambda_hat_B, lambda_hat, 
            int(clamped), clamp_type))
      
      if self.tick % self.batch_size == 0:
          self.db.commit()
  ```

### 4.2) Update agent snapshot logging

- [ ] **Include perceived prices in snapshots**
  ```python
  # In HousekeepingSystem or wherever agent snapshots are logged:
  # Store p_hat_A and p_hat_B in agent for logging
  agent._perceived_price_A = p_hat_A  # Temporary storage for telemetry
  agent._perceived_price_B = p_hat_B
  
  # Then in log_agent_snapshot(), include these:
  # perceived_price_A, perceived_price_B
  ```

---

## Part 5: Performance Optimization

### 5.1) Verify O(N) complexity

- [ ] **Profile price collection**
  ```python
  # In tests/test_kkt_performance.py (create new)
  def test_lambda_update_complexity():
      """Verify λ updates don't introduce O(N²) paths."""
      import time
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      
      # Run with increasing agent counts
      times = []
      agent_counts = [10, 20, 40, 80]
      
      for n_agents in agent_counts:
          # Modify scenario to have n_agents
          # Run for fixed ticks
          start = time.time()
          # ... run simulation ...
          elapsed = time.time() - start
          times.append(elapsed)
      
      # Check that time grows roughly linearly with N
      # (allowing for some overhead)
      ratio_1 = times[1] / times[0]
      ratio_2 = times[2] / times[1]
      
      # Should be roughly 2x (linear), not 4x (quadratic)
      assert ratio_1 < 3.0
      assert ratio_2 < 3.0
  ```

### 5.2) Optimize neighbor queries

- [ ] **Ensure spatial index used**
  ```python
  # Verify that neighbor collection uses spatial_index.query_radius()
  # Not a manual distance check over all agents
  ```

---

## Part 6: Testing

### 6.1) Unit tests for λ estimation

**File**: `tests/test_kkt_lambda_estimation.py` (create new)

- [ ] **Test λ computation**
  ```python
  def test_lambda_hat_computation():
      """Test basic λ estimation from prices."""
      # Given MU_A=2.0, p_A=4.0
      # λ_hat_A = 2.0 / 4.0 = 0.5
      assert abs(_compute_lambda_hat(mu=2.0, price=4.0) - 0.5) < 1e-9
  
  def test_lambda_min_constraint():
      """Test λ_hat_A vs λ_hat_B minimum."""
      lambda_hat_A = 1.0
      lambda_hat_B = 0.5
      lambda_hat = min(lambda_hat_A, lambda_hat_B)
      assert lambda_hat == 0.5
  ```

- [ ] **Test smoothing**
  ```python
  def test_lambda_smoothing():
      """Test exponential smoothing of λ."""
      lambda_old = 1.0
      lambda_hat = 0.5
      alpha = 0.2
      
      lambda_new = (1 - alpha) * lambda_old + alpha * lambda_hat
      expected = 0.8 * 1.0 + 0.2 * 0.5  # = 0.9
      
      assert abs(lambda_new - expected) < 1e-9
  ```

- [ ] **Test clamping**
  ```python
  def test_lambda_clamping():
      """Test λ stays within bounds."""
      lambda_hat = 1e10  # Way above bound
      lambda_max = 1e6
      
      lambda_new = min(lambda_hat, lambda_max)
      assert lambda_new == lambda_max
  ```

### 6.2) Integration tests

**File**: `tests/test_kkt_integration.py` (create new)

- [ ] **Test KKT convergence**
  ```python
  def test_kkt_lambda_converges():
      """Verify λ values stabilize over time."""
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      import sqlite3
      import tempfile
      
      with tempfile.TemporaryDirectory() as tmpdir:
          db_path = f"{tmpdir}/test.db"
          config = load_scenario("scenarios/money_test_kkt.yaml")
          log_cfg = LogConfig(use_database=True, db_path=db_path)
          
          sim = Simulation(config, seed=42, log_config=log_cfg)
          sim.run(max_ticks=100)
          sim.close()
          
          # Query lambda trajectory for agent 0
          conn = sqlite3.connect(db_path)
          cursor = conn.execute("""
              SELECT tick, lambda_money FROM agent_snapshots 
              WHERE run_id=1 AND agent_id=0 AND tick IN (10, 50, 90)
              ORDER BY tick
          """)
          lambdas = [row[1] for row in cursor.fetchall()]
          conn.close()
          
          # Check that λ changes less over time (converging)
          change_early = abs(lambdas[1] - lambdas[0])
          change_late = abs(lambdas[2] - lambdas[1])
          
          # Later changes should be smaller (or at least not much larger)
          assert change_late <= change_early * 1.5
  ```

- [ ] **Test determinism with KKT**
  ```python
  def test_kkt_deterministic():
      """Verify KKT mode is deterministic."""
      # Run same scenario twice with same seed
      # Compare lambda trajectories
      # Should be identical
      pass
  ```

### 6.3) Stress tests

- [ ] **Test λ with extreme initial values**
  ```python
  def test_lambda_from_extreme_initial():
      """Test λ converges even from extreme initial values."""
      # Set initial λ = 1e-10 (very low)
      # Run KKT estimation
      # Verify λ moves toward reasonable range
      pass
  ```

- [ ] **Test with no neighbors**
  ```python
  def test_lambda_no_neighbors():
      """Test λ update when agent has no neighbors in vision."""
      # Place agent alone on grid
      # Run tick
      # Verify: λ doesn't change (or handles gracefully)
      pass
  ```

---

## Part 7: Validation and Debugging

### 7.1) Add diagnostic logging

- [ ] **Add verbose logging for λ updates (debug mode)**
  ```python
  # In HousekeepingSystem, add optional debug prints:
  if sim.params.get('debug_lambda', False):
      print(f"Agent {agent.id}: λ {lambda_old:.4f} → {lambda_new:.4f} "
            f"(p̂_A={p_hat_A:.2f}, p̂_B={p_hat_B:.2f})")
  ```

### 7.2) Create visualization script

**File**: `scripts/plot_lambda_trajectories.py` (create new)

- [ ] **Script to plot λ over time**
  ```python
  import sqlite3
  import matplotlib.pyplot as plt
  
  def plot_lambda_trajectories(db_path: str, run_id: int):
      conn = sqlite3.connect(db_path)
      cursor = conn.execute("""
          SELECT tick, agent_id, lambda_money 
          FROM agent_snapshots 
          WHERE run_id=? 
          ORDER BY agent_id, tick
      """, (run_id,))
      
      data = {}
      for tick, agent_id, lambda_val in cursor:
          if agent_id not in data:
              data[agent_id] = {'ticks': [], 'lambdas': []}
          data[agent_id]['ticks'].append(tick)
          data[agent_id]['lambdas'].append(lambda_val)
      
      conn.close()
      
      for agent_id, values in data.items():
          plt.plot(values['ticks'], values['lambdas'], label=f'Agent {agent_id}')
      
      plt.xlabel('Tick')
      plt.ylabel('λ (Marginal Utility of Money)')
      plt.title('KKT λ Convergence')
      plt.legend()
      plt.grid(True)
      plt.show()
  
  if __name__ == '__main__':
      import sys
      plot_lambda_trajectories(sys.argv[1], int(sys.argv[2]))
  ```

- [ ] **Test visualization**
  ```bash
  python scripts/plot_lambda_trajectories.py logs/telemetry.db 1
  # Visually verify: λ values converge or stabilize
  ```

---

## Part 8: Documentation

### 8.1) Document KKT mode

- [ ] **Add section to README**
  - Explain quasi-linear vs KKT mode
  - When to use each
  - Interpretation of λ in KKT mode

- [ ] **Update typing overview**
  - Document `lambda_update_rate` parameter
  - Document `lambda_bounds` structure
  - Document `lambda_changed` flag semantics

### 8.2) Add inline documentation

- [ ] **Document median-lower rule**
- [ ] **Document cross-quote inference logic**
- [ ] **Document smoothing rationale**

---

## Completion Criteria

**Phase 3 is complete when**:

✅ KKT λ estimation implemented in HousekeepingSystem
✅ Median-lower price aggregation tested and deterministic
✅ λ smoothing with alpha parameter works correctly
✅ λ clamping to bounds enforced
✅ Cross-quote inference fallback implemented
✅ λ updates logged to telemetry
✅ Performance verified (no O(N²) paths)
✅ λ convergence demonstrated in test scenarios
✅ Visualization script works
✅ All Phase 2 tests still pass

**Ready for Phase 4 when**:
- Can run KKT scenario and observe λ values stabilizing
- Can plot λ trajectories showing convergence
- Can verify determinism across multiple runs
- Performance benchmarks show linear scaling

---

**Estimated effort**: 10-14 hours

See also:
- `money_SSOT_implementation_plan.md` §6
- `money_phase2_checklist.md` (prerequisite)
- `money_telemetry_schema.md` (lambda_updates table)

