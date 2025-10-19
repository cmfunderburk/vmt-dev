### Money Implementation — Phase 2: Monetary Exchange Basics

Author: VMT Assistant
Date: 2025-10-19

**Prerequisite**: Phase 1 complete (all infrastructure in place, no behavioral changes)

**Goal**: Implement quasi-linear utility mode with `money_only` exchange regime, enabling monetary trades.

**Success Criteria**: 
- Money trades execute successfully with correct budget constraints
- Barter is blocked when `exchange_regime = "money_only"`
- Strictly positive surplus enforcement works for money trades
- Test scenario demonstrates monetary exchange

---

## Pre-Phase 2 Verification

- [ ] **Verify Phase 1 complete**
  ```bash
  # All Phase 1 tests pass
  pytest tests/test_money_phase1.py -v
  
  # Legacy scenarios unchanged
  python scripts/compare_telemetry_snapshots.py baseline_telemetry.db logs/telemetry.db
  ```

- [ ] **Create Phase 2 branch**
  ```bash
  git checkout -b feature/money-phase2-monetary-exchange
  ```

- [ ] **Create test scenario**
  ```bash
  # Create scenarios/money_test_basic.yaml (see Part 1.1)
  ```

---

## Part 1: Test Scenario Creation

### 1.1) Create basic money scenario

**File**: `scenarios/money_test_basic.yaml` (create new)

- [ ] **Write test scenario**
  ```yaml
  schema_version: 1
  name: "Basic Monetary Exchange Test"
  N: 10
  agents: 3
  
  initial_inventories:
    A: [10, 5, 0]   # Agent 0: lots of A; Agent 1: some A; Agent 2: none
    B: [0, 5, 10]   # Agent 0: none; Agent 1: some B; Agent 2: lots of B
    M: [50, 100, 50]  # All have money
  
  utilities:
    mix:
      - type: ces
        weight: 1.0
        params:
          rho: 0.5
          wA: 0.6
          wB: 0.4
  
  params:
    spread: 0.1
    vision_radius: 10
    interaction_radius: 1
    move_budget_per_tick: 1
    dA_max: 5
    forage_rate: 1
    
    # Money system params
    exchange_regime: money_only
    money_mode: quasilinear
    money_scale: 1
    lambda_money: 1.0
  
  resource_seed:
    density: 0.1
    amount: 3
  ```

- [ ] **Verify scenario loads**
  ```bash
  python -c "from scenarios.loader import load_scenario; cfg = load_scenario('scenarios/money_test_basic.yaml'); print(f'Loaded: {cfg.name}')"
  ```

---

## Part 2: Utility Module Extensions

### 2.1) Implement quasi-linear utility functions

**File**: `src/vmt_engine/econ/utility.py`

- [ ] **Add `u_goods()` method to UCES**
  ```python
  class UCES:
      # ... existing __call__ method ...
      
      def u_goods(self, A: int, B: int) -> float:
          """
          Compute utility from goods only (excludes money).
          
          Args:
              A: Quantity of good A
              B: Quantity of good B
              
          Returns:
              Utility from goods consumption
          """
          # Extract from existing __call__ implementation
          # This is the goods-only component
          if self.rho == 0:
              # Cobb-Douglas limit
              return (A ** self.wA) * (B ** self.wB)
          else:
              term = self.wA * (A ** self.rho) + self.wB * (B ** self.rho)
              return term ** (1.0 / self.rho)
  ```

- [ ] **Add `u_goods()` method to ULinear**
  ```python
  class ULinear:
      # ... existing __call__ method ...
      
      def u_goods(self, A: int, B: int) -> float:
          """Compute utility from goods only."""
          return self.vA * A + self.vB * B
  ```

- [ ] **Add `u_total()` function**
  ```python
  def u_total(utility_func, A: int, B: int, M: int, lambda_money: float, 
              money_mode: str) -> float:
      """
      Compute total utility including money.
      
      Args:
          utility_func: UCES or ULinear instance
          A, B: Good quantities
          M: Money holdings
          lambda_money: Marginal utility of money
          money_mode: "quasilinear" or "kkt_lambda"
          
      Returns:
          Total utility
      """
      u_goods_val = utility_func.u_goods(A, B)
      
      if money_mode == "quasilinear":
          return u_goods_val + lambda_money * M
      elif money_mode == "kkt_lambda":
          # In KKT mode, utility is goods-only; lambda used only for surplus calc
          return u_goods_val
      else:
          raise ValueError(f"Unknown money_mode: {money_mode}")
  ```

- [ ] **Test utility functions**
  ```python
  # In tests/test_utility_money.py (create new)
  def test_uces_u_goods():
      from vmt_engine.econ.utility import UCES
      util = UCES(rho=0.5, wA=0.6, wB=0.4)
      
      u_goods = util.u_goods(10, 5)
      assert u_goods > 0
      
      # u_goods should not depend on M
      u_total_1 = u_total(util, 10, 5, 0, 1.0, "quasilinear")
      u_total_2 = u_total(util, 10, 5, 100, 1.0, "quasilinear")
      assert u_total_2 == u_total_1 + 100  # Linear in M
  ```

### 2.2) Expose marginal utilities

- [ ] **Add `mu_A()` and `mu_B()` methods to UCES**
  ```python
  class UCES:
      def mu_A(self, A: int, B: int, epsilon: float = 1e-12) -> float:
          """Marginal utility of good A."""
          # May already exist; if not, implement
          # MU_A = ∂u/∂A using CES formula
          if self.rho == 0:
              # Cobb-Douglas
              return self.wA * (B / max(A, epsilon)) ** (1 - self.wA)
          else:
              u_val = self.u_goods(A, B)
              term = self.wA * (A ** self.rho) + self.wB * (B ** self.rho)
              return self.wA * (A ** (self.rho - 1)) * (term ** ((1/self.rho) - 1))
      
      def mu_B(self, A: int, B: int, epsilon: float = 1e-12) -> float:
          """Marginal utility of good B."""
          # Similar to mu_A
          if self.rho == 0:
              return self.wB * (A / max(B, epsilon)) ** self.wA
          else:
              term = self.wA * (A ** self.rho) + self.wB * (B ** self.rho)
              return self.wB * (B ** (self.rho - 1)) * (term ** ((1/self.rho) - 1))
  ```

- [ ] **Add `mu_A()` and `mu_B()` to ULinear**
  ```python
  class ULinear:
      def mu_A(self, A: int, B: int, epsilon: float = 1e-12) -> float:
          """Marginal utility of good A."""
          return self.vA
      
      def mu_B(self, A: int, B: int, epsilon: float = 1e-12) -> float:
          """Marginal utility of good B."""
          return self.vB
  ```

- [ ] **Test marginal utilities**
  ```python
  def test_marginal_utilities():
      from vmt_engine.econ.utility import UCES
      util = UCES(rho=0.5, wA=0.6, wB=0.4)
      
      mu_a = util.mu_A(10, 5)
      mu_b = util.mu_B(10, 5)
      
      assert mu_a > 0
      assert mu_b > 0
      
      # Check numerical derivative approximation
      delta = 0.01
      u1 = util.u_goods(10, 5)
      u2 = util.u_goods(10 + delta, 5)
      mu_a_numeric = (u2 - u1) / delta
      
      assert abs(mu_a - mu_a_numeric) < 0.1  # Reasonable tolerance
  ```

---

## Part 3: Quotes System Generalization

### 3.1) Extend quote computation for money

**File**: `src/vmt_engine/systems/quotes.py`

- [ ] **Add money reservation prices to `compute_quotes()`**
  ```python
  def compute_quotes(agent: Agent, spread: float, epsilon: float) -> dict:
      """
      Compute reservation prices for all permissible exchange pairs.
      
      Returns:
          dict with keys like 'ask_A_in_B', 'ask_A_in_M', etc.
      """
      from vmt_engine.econ.utility import u_total
      
      # Get marginal utilities
      mu_A = agent.utility.mu_A(agent.inventory.A, agent.inventory.B, epsilon)
      mu_B = agent.utility.mu_B(agent.inventory.A, agent.inventory.B, epsilon)
      
      quotes = {}
      
      # Goods-for-goods (existing logic)
      p_star_A_in_B = mu_A / max(mu_B, epsilon)
      p_star_B_in_A = mu_B / max(mu_A, epsilon)
      
      # Apply spread (existing)
      ask_A_in_B = p_star_A_in_B * (1 + spread)
      bid_A_in_B = p_star_A_in_B * (1 - spread)
      
      # Clamp (existing)
      p_min = epsilon
      p_max = 1e6
      quotes['ask_A_in_B'] = max(ask_A_in_B, p_min)
      quotes['bid_A_in_B'] = min(bid_A_in_B, p_max)
      # ... similar for B_in_A ...
      
      # NEW: Goods-for-money
      # p*_{A in M} = MU_A / λ
      p_star_A_in_M = mu_A / max(agent.lambda_money, epsilon)
      p_star_B_in_M = mu_B / max(agent.lambda_money, epsilon)
      
      ask_A_in_M = p_star_A_in_M * (1 + spread)
      bid_A_in_M = p_star_A_in_M * (1 - spread)
      ask_B_in_M = p_star_B_in_M * (1 + spread)
      bid_B_in_M = p_star_B_in_M * (1 - spread)
      
      quotes['ask_A_in_M'] = max(ask_A_in_M, p_min)
      quotes['bid_A_in_M'] = min(bid_A_in_M, p_max)
      quotes['ask_B_in_M'] = max(ask_B_in_M, p_min)
      quotes['bid_B_in_M'] = min(bid_B_in_M, p_max)
      
      return quotes
  ```

- [ ] **Update Agent to store money quotes**
  ```python
  # In Agent dataclass (core/state.py), ensure quotes dict can hold money quotes
  # May need to update how quotes are stored/accessed
  ```

- [ ] **Test quote computation**
  ```python
  def test_money_quotes():
      from vmt_engine.systems.quotes import compute_quotes
      from vmt_engine.core.state import Agent, Inventory
      from vmt_engine.econ.utility import UCES
      
      util = UCES(rho=0.5, wA=0.6, wB=0.4)
      agent = Agent(
          id=0, pos=(0,0),
          inventory=Inventory(A=10, B=5, M=50),
          utility=util,
          vision_radius=5,
          move_budget_per_tick=1
      )
      agent.lambda_money = 1.0
      
      quotes = compute_quotes(agent, spread=0.1, epsilon=1e-12)
      
      assert 'ask_A_in_M' in quotes
      assert 'bid_A_in_M' in quotes
      assert quotes['ask_A_in_M'] > 0
  ```

### 3.2) Filter quotes by exchange_regime

- [ ] **Add regime filtering in HousekeepingSystem**
  ```python
  # In HousekeepingSystem.execute():
  for agent in sim.agents:
      if agent.inventory_changed:
          all_quotes = compute_quotes(agent, sim.params['spread'], sim.params['epsilon'])
          
          # Filter by exchange_regime
          regime = sim.params['exchange_regime']
          agent.quotes = filter_quotes_by_regime(all_quotes, regime)
          
          agent.inventory_changed = False
  ```

- [ ] **Implement `filter_quotes_by_regime()` helper**
  ```python
  def filter_quotes_by_regime(all_quotes: dict, regime: str) -> dict:
      """Filter quotes to only include permissible exchange pairs."""
      if regime == "barter_only":
          return {k: v for k, v in all_quotes.items() if '_in_M' not in k}
      elif regime == "money_only":
          return {k: v for k, v in all_quotes.items() if '_in_M' in k}
      elif regime in ["mixed", "mixed_liquidity_gated"]:
          return all_quotes  # All pairs allowed
      else:
          return {}
  ```

---

## Part 4: Trading System Extensions

### 4.1) Generalize `find_compensating_block()` for money

**File**: `src/vmt_engine/systems/trading.py` (or `matching.py`)

- [ ] **Add generic trade search function**
  ```python
  def find_compensating_block_generic(
      buyer: Agent, seller: Agent, 
      good_sold: str,  # "A", "B", or "M"
      good_paid: str,  # "A", "B", or "M"
      price_paid_per_sold: float,
      dX_max: int,
      epsilon: float
  ) -> tuple[int, int, float, float] | None:
      """
      Find mutually beneficial trade for generic good pair.
      
      Returns:
          (dX, dY, buyer_surplus, seller_surplus) or None if no trade found
      """
      for dX in range(1, dX_max + 1):
          # Compute dY using round-half-up
          dY = int(price_paid_per_sold * dX + 0.5)
          
          # Get current inventories
          buyer_inv = {
              'A': buyer.inventory.A, 
              'B': buyer.inventory.B, 
              'M': buyer.inventory.M
          }
          seller_inv = {
              'A': seller.inventory.A,
              'B': seller.inventory.B,
              'M': seller.inventory.M
          }
          
          # Check feasibility
          if seller_inv[good_sold] < dX:
              continue
          if buyer_inv[good_paid] < dY:
              continue
          
          # Compute new inventories
          buyer_new = buyer_inv.copy()
          buyer_new[good_sold] += dX
          buyer_new[good_paid] -= dY
          
          seller_new = seller_inv.copy()
          seller_new[good_sold] -= dX
          seller_new[good_paid] += dY
          
          # Compute surplus
          if good_paid == 'M':
              # Buyer pays money
              buyer_u_old = buyer.utility.u_goods(buyer_inv['A'], buyer_inv['B'])
              buyer_u_new = buyer.utility.u_goods(buyer_new['A'], buyer_new['B'])
              buyer_surplus = buyer_u_new - buyer_u_old - buyer.lambda_money * dY
              
              seller_u_old = seller.utility.u_goods(seller_inv['A'], seller_inv['B'])
              seller_u_new = seller.utility.u_goods(seller_new['A'], seller_new['B'])
              seller_surplus = seller_u_new - seller_u_old + seller.lambda_money * dY
          else:
              # Barter (goods for goods)
              buyer_u_old = buyer.utility.u_goods(buyer_inv['A'], buyer_inv['B'])
              buyer_u_new = buyer.utility.u_goods(buyer_new['A'], buyer_new['B'])
              buyer_surplus = buyer_u_new - buyer_u_old
              
              seller_u_old = seller.utility.u_goods(seller_inv['A'], seller_inv['B'])
              seller_u_new = seller.utility.u_goods(seller_new['A'], seller_new['B'])
              seller_surplus = seller_u_new - seller_u_old
          
          # Check strictly positive
          if buyer_surplus > epsilon and seller_surplus > epsilon:
              return (dX, dY, buyer_surplus, seller_surplus)
      
      return None
  ```

### 4.2) Update TradeSystem to respect exchange_regime

**File**: `src/vmt_engine/systems/trading.py`

- [ ] **Modify TradeSystem.execute() to filter by regime**
  ```python
  class TradeSystem:
      def execute(self, sim: "Simulation") -> None:
          # Respect mode_schedule (temporal control)
          if sim.current_mode not in ["trade", "both"]:
              return
          
          # Get permissible exchange pairs based on regime
          regime = sim.params['exchange_regime']
          allowed_pairs = self._get_allowed_pairs(regime)
          
          # ... existing trade matching logic, but only consider allowed_pairs ...
      
      def _get_allowed_pairs(self, regime: str) -> list[tuple[str, str]]:
          """Get allowed (good_sold, good_paid) pairs."""
          if regime == "barter_only":
              return [("A", "B"), ("B", "A")]
          elif regime == "money_only":
              return [("A", "M"), ("B", "M")]
          elif regime in ["mixed", "mixed_liquidity_gated"]:
              return [("A", "M"), ("B", "M"), ("A", "B"), ("B", "A")]
          else:
              return []
  ```

- [ ] **Update trade execution to handle money transfers**
  ```python
  def execute_trade(buyer: Agent, seller: Agent, 
                   good_sold: str, good_paid: str, 
                   dX: int, dY: int) -> None:
      """Execute a trade, updating inventories."""
      # Update buyer
      if good_sold == "A":
          buyer.inventory.A += dX
      elif good_sold == "B":
          buyer.inventory.B += dX
      elif good_sold == "M":
          buyer.inventory.M += dX
      
      if good_paid == "A":
          buyer.inventory.A -= dY
      elif good_paid == "B":
          buyer.inventory.B -= dY
      elif good_paid == "M":
          buyer.inventory.M -= dY
      
      # Update seller (opposite)
      if good_sold == "A":
          seller.inventory.A -= dX
      elif good_sold == "B":
          seller.inventory.B -= dX
      elif good_sold == "M":
          seller.inventory.M -= dX
      
      if good_paid == "A":
          seller.inventory.A += dY
      elif good_paid == "B":
          seller.inventory.B += dY
      elif good_paid == "M":
          seller.inventory.M += dY
      
      # Set inventory_changed flags
      buyer.inventory_changed = True
      seller.inventory_changed = True
  ```

---

## Part 5: Telemetry Integration

### 5.1) Update trade logging to include money

**File**: `src/telemetry/db_loggers.py`

- [ ] **Extend `log_trade()` signature**
  ```python
  def log_trade(self, tick: int, x: int, y: int,
                buyer_id: int, seller_id: int,
                dA: int, dB: int, dM: int,  # NEW
                price: float, direction: str,
                exchange_pair_type: str,  # NEW
                buyer_lambda: float = None, seller_lambda: float = None,  # NEW
                buyer_surplus: float = None, seller_surplus: float = None  # NEW
                ) -> None:
      """Log a completed trade."""
      if not self.config.use_database or self.db is None:
          return
      
      self.db.execute("""
          INSERT INTO trades 
          (run_id, tick, x, y, buyer_id, seller_id, dA, dB, dM, 
           price, direction, exchange_pair_type, 
           buyer_lambda, seller_lambda, buyer_surplus, seller_surplus)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (self.run_id, tick, x, y, buyer_id, seller_id, dA, dB, dM,
            price, direction, exchange_pair_type,
            buyer_lambda, seller_lambda, buyer_surplus, seller_surplus))
      
      if self.tick % self.batch_size == 0:
          self.db.commit()
  ```

- [ ] **Update TradeSystem to call with money params**
  ```python
  # In TradeSystem, after executing trade:
  if sim.telemetry:
      # Compute dA, dB, dM based on which goods were traded
      dA = dX if good_sold == "A" else (-dY if good_paid == "A" else 0)
      dB = dX if good_sold == "B" else (-dY if good_paid == "B" else 0)
      dM = dY if good_paid == "M" else (-dX if good_sold == "M" else 0)
      
      pair_type = f"{good_sold}<->{good_paid}"
      price = dY / dX  # Or appropriate price calculation
      
      sim.telemetry.log_trade(
          tick=sim.tick, x=buyer.pos[0], y=buyer.pos[1],
          buyer_id=buyer.id, seller_id=seller.id,
          dA=dA, dB=dB, dM=dM,
          price=price, direction=direction,
          exchange_pair_type=pair_type,
          buyer_lambda=buyer.lambda_money if dM != 0 else None,
          seller_lambda=seller.lambda_money if dM != 0 else None,
          buyer_surplus=buyer_surplus,
          seller_surplus=seller_surplus
      )
  ```

### 5.2) Update agent snapshot logging

**File**: `src/telemetry/db_loggers.py`

- [ ] **Extend `log_agent_snapshot()` to include M and money quotes**
  ```python
  def log_agent_snapshot(self, tick: int, agent: Agent, 
                         utility_val: float, 
                         quotes: dict) -> None:
      """Log agent state snapshot."""
      if not self.config.use_database or self.db is None:
          return
      
      self.db.execute("""
          INSERT INTO agent_snapshots 
          (run_id, tick, agent_id, x, y, 
           inventory_A, inventory_B, inventory_M,
           utility, 
           ask_A_in_B, bid_A_in_B, p_min, p_max,
           ask_A_in_M, bid_A_in_M, ask_B_in_M, bid_B_in_M,
           lambda_money, lambda_changed,
           target_agent_id, target_x, target_y, utility_type)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (
          self.run_id, tick, agent.id, agent.pos[0], agent.pos[1],
          agent.inventory.A, agent.inventory.B, agent.inventory.M,
          utility_val,
          quotes.get('ask_A_in_B'), quotes.get('bid_A_in_B'), 
          quotes.get('p_min', 0), quotes.get('p_max', 1e6),
          quotes.get('ask_A_in_M'), quotes.get('bid_A_in_M'),
          quotes.get('ask_B_in_M'), quotes.get('bid_B_in_M'),
          agent.lambda_money, int(agent.lambda_changed),
          # ... targets, utility_type ...
      ))
  ```

---

## Part 6: Testing

### 6.1) Unit tests

**File**: `tests/test_money_phase2.py` (create new)

- [ ] **Test money trade mechanics**
  ```python
  def test_money_trade_budget_constraint():
      """Verify money trades respect budget constraints."""
      # Create two agents: one with A+money, one with B+money
      # Execute A<->M trade
      # Verify: buyer's M decreases, seller's M increases by same amount
      # Verify: inventories satisfy conservation
      pass
  
  def test_strict_surplus_enforcement():
      """Verify trades only execute if both surpluses > 0."""
      # Create agents where trade would benefit one but not other
      # Attempt trade
      # Verify: no trade occurs
      pass
  
  def test_barter_blocked_in_money_only():
      """Verify barter trades don't occur when exchange_regime=money_only."""
      # Create scenario with money_only regime
      # Place two agents adjacent with complementary goods
      # Run tick
      # Verify: no barter trade occurred
      pass
  ```

### 6.2) Integration test

**File**: `tests/test_money_phase2_integration.py` (create new)

- [ ] **Test complete money scenario**
  ```python
  def test_money_scenario_runs():
      """Run full money_test_basic.yaml scenario."""
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      import tempfile
      
      with tempfile.TemporaryDirectory() as tmpdir:
          db_path = f"{tmpdir}/test.db"
          config = load_scenario("scenarios/money_test_basic.yaml")
          log_cfg = LogConfig(use_database=True, db_path=db_path)
          
          sim = Simulation(config, seed=42, log_config=log_cfg)
          sim.run(max_ticks=50)
          sim.close()
          
          # Query database for money trades
          import sqlite3
          conn = sqlite3.connect(db_path)
          cursor = conn.execute("SELECT COUNT(*) FROM trades WHERE dM > 0")
          money_trade_count = cursor.fetchone()[0]
          conn.close()
          
          assert money_trade_count > 0, "Expected at least one money trade"
  ```

- [ ] **Test money conservation**
  ```python
  def test_money_conservation():
      """Verify total money supply is conserved."""
      # Run scenario
      # Query initial total M from agent_snapshots at tick=0
      # Query final total M from agent_snapshots at tick=max
      # Verify: initial_total == final_total
      pass
  ```

### 6.3) Regression test

- [ ] **Verify barter scenarios still work**
  ```bash
  pytest tests/test_money_phase1.py -v
  # Should still pass - Phase 2 doesn't break legacy
  ```

---

## Part 7: Documentation

### 7.1) Update user documentation

- [ ] **Document money scenarios in README**
  - Add section explaining money_mode, exchange_regime
  - Show example YAML snippet
  - Explain λ parameter meaning

- [ ] **Update typing overview**
  - Document Inventory.M field
  - Document money quote fields
  - Document exchange_pair_type values

### 7.2) Add code comments

- [ ] **Document quasi-linear utility assumption**
- [ ] **Document surplus calculation for money trades**
- [ ] **Document exchange_regime enforcement**

---

## Completion Criteria

**Phase 2 is complete when**:

✅ Quasi-linear utility mode implemented and tested
✅ Money quotes computed correctly from `MU_G / λ`
✅ `exchange_regime = "money_only"` blocks barter, permits monetary trades
✅ Money trades execute with correct surplus calculation
✅ Money conservation verified
✅ Test scenario demonstrates successful monetary exchange
✅ Telemetry logs money transfers correctly
✅ All Phase 1 tests still pass (no regressions)

**Ready for Phase 3 when**:
- Can run money_test_basic.yaml and observe trades in log viewer
- Can verify in database that dM columns are populated
- Money inventories change over time but total supply is conserved

---

**Estimated effort**: 8-12 hours

See also:
- `money_SSOT_implementation_plan.md` §0-7
- `money_phase1_checklist.md` (prerequisite)
- `money_telemetry_schema.md` (database reference)

