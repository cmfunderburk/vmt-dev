### Money Implementation — Phase 1 Developer Checklist

Author: VMT Assistant
Date: 2025-10-19

This checklist provides a detailed, step-by-step guide for implementing **Phase 1: Infrastructure** of the money introduction, ensuring no behavioral changes to existing scenarios.

**Goal**: Add all money-related fields and infrastructure with defaults that preserve legacy behavior perfectly.

**Success Criteria**: All existing scenarios run identically before and after Phase 1 changes.

---

## Pre-Implementation

### Setup and Baseline

- [ ] **Create feature branch**
  ```bash
  git checkout -b feature/money-phase1-infrastructure
  ```

- [ ] **Run existing test suite and record results**
  ```bash
  pytest -v > baseline_tests.txt
  ```

- [ ] **Run a legacy scenario and capture telemetry snapshot**
  ```bash
  python main.py scenarios/three_agent_barter.yaml --seed 42
  # Save logs/telemetry.db as baseline_telemetry.db for comparison
  cp logs/telemetry.db baseline_telemetry.db
  ```

- [ ] **Document current schema**
  ```bash
  sqlite3 baseline_telemetry.db ".schema" > baseline_schema.sql
  ```

---

## Part 1: Schema Layer (No Behavior Changes)

### 1.1) Add money fields to `ScenarioParams`

**File**: `src/scenarios/schema.py`

- [ ] **Add imports**
  ```python
  from typing import Literal  # if not already imported
  ```

- [ ] **Add money fields to `ScenarioParams` class**
  ```python
  @dataclass
  class ScenarioParams:
      # ... existing fields ...
      
      # Money system parameters (Phase 1)
      exchange_regime: Literal["barter_only", "money_only", "mixed", "mixed_liquidity_gated"] = "barter_only"
      money_mode: Literal["quasilinear", "kkt_lambda"] = "quasilinear"
      money_scale: int = 1
      lambda_money: float = 1.0
      lambda_update_rate: float = 0.2
      lambda_bounds: dict[str, float] = field(default_factory=lambda: {"lambda_min": 1e-6, "lambda_max": 1e6})
      liquidity_gate: dict[str, int] = field(default_factory=lambda: {"min_quotes": 3})
      earn_money_enabled: bool = False
  ```

- [ ] **Add validation for money params in `ScenarioParams.validate()`**
  ```python
  # In ScenarioParams.validate() method, after existing validation:
  
  # Money system validation
  if self.money_scale < 1:
      raise ValueError(f"money_scale must be >= 1, got {self.money_scale}")
  
  if self.lambda_money <= 0:
      raise ValueError(f"lambda_money must be positive, got {self.lambda_money}")
  
  if self.lambda_update_rate < 0 or self.lambda_update_rate > 1:
      raise ValueError(f"lambda_update_rate must be in [0, 1], got {self.lambda_update_rate}")
  
  if "lambda_min" in self.lambda_bounds and "lambda_max" in self.lambda_bounds:
      if self.lambda_bounds["lambda_min"] >= self.lambda_bounds["lambda_max"]:
          raise ValueError("lambda_min must be < lambda_max")
      if self.lambda_bounds["lambda_min"] <= 0:
          raise ValueError("lambda_min must be positive")
  
  if "min_quotes" in self.liquidity_gate:
      if self.liquidity_gate["min_quotes"] < 0:
          raise ValueError("liquidity_gate.min_quotes must be non-negative")
  ```

- [ ] **Test: Verify defaults don't break existing scenarios**
  ```bash
  pytest tests/test_scenario_schema.py -v
  ```

### 1.2) Extend `ScenarioConfig` to support M inventory

**File**: `src/scenarios/schema.py`

- [ ] **Update `ScenarioConfig.validate()` to check money constraints**
  ```python
  # In ScenarioConfig.validate(), after existing inventory validation:
  
  # Money inventory validation
  if self.params.exchange_regime in ["money_only", "mixed", "mixed_liquidity_gated"]:
      if "M" not in self.initial_inventories:
          raise ValueError(
              f"exchange_regime={self.params.exchange_regime} requires M in initial_inventories"
          )
  ```

### 1.3) Update scenario loader

**File**: `src/scenarios/loader.py`

- [ ] **Add parsing for money params** (in `load_scenario()` function)
  ```python
  # After parsing existing params:
  
  # Parse money params (optional, with defaults)
  exchange_regime = params_data.get("exchange_regime", "barter_only")
  money_mode = params_data.get("money_mode", "quasilinear")
  money_scale = params_data.get("money_scale", 1)
  lambda_money = params_data.get("lambda_money", 1.0)
  lambda_update_rate = params_data.get("lambda_update_rate", 0.2)
  lambda_bounds = params_data.get("lambda_bounds", {"lambda_min": 1e-6, "lambda_max": 1e6})
  liquidity_gate = params_data.get("liquidity_gate", {"min_quotes": 3})
  earn_money_enabled = params_data.get("earn_money_enabled", False)
  
  # Add to ScenarioParams construction:
  params = ScenarioParams(
      # ... existing params ...
      exchange_regime=exchange_regime,
      money_mode=money_mode,
      money_scale=money_scale,
      lambda_money=lambda_money,
      lambda_update_rate=lambda_update_rate,
      lambda_bounds=lambda_bounds,
      liquidity_gate=liquidity_gate,
      earn_money_enabled=earn_money_enabled,
  )
  ```

- [ ] **Parse M from `initial_inventories`**
  ```python
  # After parsing A and B inventories:
  
  # Parse M inventory (optional, defaults to 0)
  inv_M = data['initial_inventories'].get('M', 0)
  if isinstance(inv_M, int):
      inv_M = [inv_M] * n_agents
  if isinstance(inv_M, list) and len(inv_M) != n_agents:
      raise ValueError(f"M inventory list must match agent count {n_agents}")
  
  # Store inv_M for later use (see Part 2)
  ```

- [ ] **Test: Load existing scenarios without M**
  ```bash
  python -c "from scenarios.loader import load_scenario; load_scenario('scenarios/three_agent_barter.yaml')"
  ```

- [ ] **Test: Validate new field parsing**
  ```bash
  pytest tests/test_scenario_loader.py -v
  ```

---

## Part 2: Core State Extensions (Prepare for Money)

### 2.1) Extend `Inventory` dataclass

**File**: `src/vmt_engine/core/state.py`

- [ ] **Add M field to `Inventory`**
  ```python
  @dataclass
  class Inventory:
      A: int = 0
      B: int = 0
      M: int = 0  # NEW: Money in minor units
      
      def __post_init__(self):
          # Validate invariants
          if self.A < 0 or self.B < 0 or self.M < 0:
              raise ValueError("Inventory quantities must be non-negative")
  ```

- [ ] **Update any `Inventory()` constructor calls in tests**
  - Search for `Inventory(` patterns
  - Ensure tests don't break with new field (defaults to 0)

- [ ] **Test: Verify inventory validation**
  ```python
  # In tests/test_core_state.py
  def test_inventory_money_nonnegative():
      inv = Inventory(A=5, B=10, M=100)
      assert inv.M == 100
      
      with pytest.raises(ValueError):
          Inventory(A=5, B=10, M=-1)
  ```

### 2.2) Extend `Agent` state

**File**: `src/vmt_engine/core/state.py`

- [ ] **Add money-related agent fields**
  ```python
  @dataclass
  class Agent:
      # ... existing fields ...
      
      # Money system state (Phase 1)
      lambda_money: float = 1.0  # Marginal utility of money
      lambda_changed: bool = False  # Flag for Housekeeping
      
      # Note: inventory already has M field from Inventory extension
  ```

- [ ] **Test: Verify agent creation with defaults**
  ```python
  # In tests/test_core_state.py
  def test_agent_money_defaults():
      agent = Agent(
          id=0, pos=(0, 0), 
          inventory=Inventory(A=5, B=5, M=0),
          utility=None,
          vision_radius=5,
          move_budget_per_tick=1
      )
      assert agent.lambda_money == 1.0
      assert agent.lambda_changed == False
  ```

### 2.3) Extend `Quote` handling (prepare for money pairs)

**File**: `src/vmt_engine/core/state.py`

- [ ] **Document quote extension plan** (no code changes yet)
  ```python
  # Add comment to Quote or quotes field:
  # TODO Phase 2: Extend to support (A,M), (M,A), (B,M), (M,B) pairs
  # For now, only (A,B) and (B,A) stored (backward compatible)
  ```

---

## Part 3: Telemetry Extensions (Log Infrastructure)

### 3.1) Extend database schema

**File**: `src/telemetry/database.py`

- [ ] **Add money columns to existing tables in `_create_schema()`**

  ```python
  # In _create_schema(), after existing simulation_runs table:
  cursor.execute("""
      CREATE TABLE IF NOT EXISTS simulation_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          scenario_name TEXT,
          start_time TEXT,
          end_time TEXT,
          total_ticks INTEGER,
          num_agents INTEGER,
          grid_width INTEGER,
          grid_height INTEGER,
          config_json TEXT,
          exchange_regime TEXT DEFAULT 'barter_only',
          money_mode TEXT DEFAULT NULL,
          money_scale INTEGER DEFAULT 1
      )
  """)
  ```

  ```python
  # In agent_snapshots table (add these columns):
  # ... existing columns ...
  inventory_M INTEGER DEFAULT 0,
  lambda_money REAL DEFAULT NULL,
  ask_A_in_M REAL DEFAULT NULL,
  bid_A_in_M REAL DEFAULT NULL,
  ask_B_in_M REAL DEFAULT NULL,
  bid_B_in_M REAL DEFAULT NULL,
  perceived_price_A REAL DEFAULT NULL,
  perceived_price_B REAL DEFAULT NULL,
  lambda_changed INTEGER DEFAULT 0,
  # ... rest of table ...
  ```

  ```python
  # In trades table (add these columns):
  # ... existing columns ...
  dM INTEGER DEFAULT 0,
  exchange_pair_type TEXT DEFAULT 'A<->B',
  buyer_lambda REAL DEFAULT NULL,
  seller_lambda REAL DEFAULT NULL,
  buyer_surplus REAL DEFAULT NULL,
  seller_surplus REAL DEFAULT NULL,
  # ... rest of table ...
  ```

- [ ] **Create new `tick_states` table**
  ```python
  # After mode_changes table:
  cursor.execute("""
      CREATE TABLE IF NOT EXISTS tick_states (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id INTEGER NOT NULL,
          tick INTEGER NOT NULL,
          current_mode TEXT NOT NULL,
          exchange_regime TEXT NOT NULL,
          active_pairs TEXT NOT NULL,
          FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id),
          UNIQUE(run_id, tick)
      )
  """)
  
  cursor.execute("""
      CREATE INDEX IF NOT EXISTS idx_tick_states_run_tick 
      ON tick_states(run_id, tick)
  """)
  ```

- [ ] **Create new `lambda_updates` table**
  ```python
  # After tick_states table:
  cursor.execute("""
      CREATE TABLE IF NOT EXISTS lambda_updates (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id INTEGER NOT NULL,
          tick INTEGER NOT NULL,
          agent_id INTEGER NOT NULL,
          lambda_old REAL NOT NULL,
          lambda_new REAL NOT NULL,
          lambda_hat_A REAL NOT NULL,
          lambda_hat_B REAL NOT NULL,
          lambda_hat REAL NOT NULL,
          clamped INTEGER NOT NULL,
          clamp_type TEXT,
          FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
      )
  """)
  
  cursor.execute("""
      CREATE INDEX IF NOT EXISTS idx_lambda_updates_run_agent 
      ON lambda_updates(run_id, agent_id, tick)
  """)
  ```

- [ ] **Test: Verify schema creates without errors**
  ```bash
  rm -f test_telemetry.db
  python -c "from telemetry.database import TelemetryDatabase; db = TelemetryDatabase('test_telemetry.db'); print('Schema created successfully')"
  sqlite3 test_telemetry.db ".schema" > new_schema.sql
  # Verify new columns present
  ```

### 3.2) Add telemetry logging methods (stubs for now)

**File**: `src/telemetry/db_loggers.py`

- [ ] **Add `log_tick_state()` method**
  ```python
  def log_tick_state(self, tick: int, current_mode: str, 
                     exchange_regime: str, active_pairs: list[str]):
      """Log tick-level mode and exchange regime state."""
      if not self.config.use_database or self.db is None:
          return
      
      import json
      self.db.execute("""
          INSERT INTO tick_states (run_id, tick, current_mode, exchange_regime, active_pairs)
          VALUES (?, ?, ?, ?, ?)
      """, (self.run_id, tick, current_mode, exchange_regime, json.dumps(active_pairs)))
      
      if self.tick % self.batch_size == 0:
          self.db.commit()
  ```

- [ ] **Add `log_lambda_update()` method stub**
  ```python
  def log_lambda_update(self, tick: int, agent_id: int, 
                       lambda_old: float, lambda_new: float,
                       lambda_hat_A: float, lambda_hat_B: float, lambda_hat: float,
                       clamped: bool, clamp_type: str = None):
      """Log KKT lambda update (Phase 3 implementation)."""
      if not self.config.use_database or self.db is None:
          return
      
      # Phase 1: Just stub, will implement in Phase 3
      pass
  ```

- [ ] **Update `create_run()` to accept money params**
  ```python
  # Modify signature to accept exchange_regime, money_mode, money_scale
  # Store them in simulation_runs table
  ```

---

## Part 4: Simulation Integration (Wire Up State, No Logic Yet)

### 4.1) Update agent initialization to handle M

**File**: `src/vmt_engine/simulation.py`

- [ ] **Parse M inventory in `_initialize_agents()`**
  ```python
  # In _initialize_agents(), after parsing A and B:
  
  # Parse M inventory (defaults to 0 if not present)
  inv_M = self.config.initial_inventories.get('M', 0)
  if isinstance(inv_M, int):
      inv_M = [inv_M] * n_agents
  if isinstance(inv_M, list) and len(inv_M) != n_agents:
      raise ValueError(f"M inventory list must match agent count {n_agents}")
  
  # Later, when creating inventory:
  inventory = Inventory(A=inv_A[i], B=inv_B[i], M=inv_M[i])
  ```

- [ ] **Initialize agent lambda_money from params**
  ```python
  # After creating agent:
  agent.lambda_money = self.params['lambda_money']
  agent.lambda_changed = False
  ```

- [ ] **Add money params to self.params dict in `__init__()`**
  ```python
  self.params = {
      # ... existing params ...
      'exchange_regime': scenario_config.params.exchange_regime,
      'money_mode': scenario_config.params.money_mode,
      'money_scale': scenario_config.params.money_scale,
      'lambda_money': scenario_config.params.lambda_money,
      'lambda_update_rate': scenario_config.params.lambda_update_rate,
      'lambda_bounds': scenario_config.params.lambda_bounds,
      'liquidity_gate': scenario_config.params.liquidity_gate,
      'earn_money_enabled': scenario_config.params.earn_money_enabled,
  }
  ```

### 4.2) Update telemetry initialization

**File**: `src/vmt_engine/simulation.py`

- [ ] **Pass money config to telemetry `start_run()`**
  ```python
  # In __init__, when calling telemetry.start_run():
  import json
  config_dict = {
      'seed': seed, 
      'params': self.params,
      'exchange_regime': self.config.params.exchange_regime,
      'money_mode': self.config.params.money_mode,
      'money_scale': self.config.params.money_scale,
  }
  
  self.telemetry.start_run(
      num_agents=len(self.agents),
      grid_width=self.config.N,
      grid_height=self.config.N,
      config_dict=config_dict  # Pass enhanced config
  )
  ```

### 4.3) Add helper method for active exchange pairs

**File**: `src/vmt_engine/simulation.py`

- [ ] **Add `_get_active_exchange_pairs()` method**
  ```python
  def _get_active_exchange_pairs(self) -> list[str]:
      """
      Determine which exchange pairs are currently active.
      Used for telemetry (Option A-plus observability).
      """
      if self.current_mode == "forage":
          return []  # No trading during forage mode
      
      regime = self.params['exchange_regime']
      
      if regime == "barter_only":
          return ["A<->B"]
      elif regime == "money_only":
          return ["A<->M", "B<->M"]
      elif regime in ["mixed", "mixed_liquidity_gated"]:
          # Phase 1: report all possible pairs; Phase 4 will refine for liquidity gating
          return ["A<->M", "B<->M", "A<->B"]
      else:
          return []
  ```

- [ ] **Call in `step()` to log tick state**
  ```python
  # In step(), after determining current_mode:
  if self.telemetry:
      active_pairs = self._get_active_exchange_pairs()
      self.telemetry.log_tick_state(
          self.tick,
          self.current_mode,
          self.params['exchange_regime'],
          active_pairs
      )
  ```

---

## Part 5: Testing and Validation

### 5.1) Unit tests for new components

**File**: `tests/test_money_phase1.py` (create new)

- [ ] **Test schema validation**
  ```python
  def test_money_params_defaults():
      """Verify default money params don't break existing scenarios."""
      from scenarios.schema import ScenarioParams
      params = ScenarioParams()
      assert params.exchange_regime == "barter_only"
      assert params.money_scale == 1
      params.validate()  # Should not raise
  
  def test_money_params_validation():
      """Verify money param validation."""
      from scenarios.schema import ScenarioParams
      
      # Invalid money_scale
      with pytest.raises(ValueError):
          p = ScenarioParams(money_scale=0)
          p.validate()
      
      # Invalid lambda bounds
      with pytest.raises(ValueError):
          p = ScenarioParams(lambda_bounds={"lambda_min": 1.0, "lambda_max": 0.5})
          p.validate()
  ```

- [ ] **Test inventory extension**
  ```python
  def test_inventory_with_money():
      """Verify Inventory accepts M field."""
      from vmt_engine.core.state import Inventory
      inv = Inventory(A=10, B=20, M=100)
      assert inv.M == 100
  ```

- [ ] **Test agent money state**
  ```python
  def test_agent_lambda_initialization():
      """Verify agents initialize with lambda_money."""
      from vmt_engine.core.state import Agent, Inventory
      agent = Agent(
          id=0, pos=(0,0), 
          inventory=Inventory(A=5, B=5, M=50),
          utility=None, vision_radius=5, move_budget_per_tick=1
      )
      assert agent.lambda_money == 1.0
      assert agent.inventory.M == 50
  ```

### 5.2) Integration test: Legacy scenario unchanged

**File**: `tests/test_money_phase1_integration.py` (create new)

- [ ] **Test: Run existing scenario, verify identical behavior**
  ```python
  def test_legacy_scenario_unchanged():
      """Verify legacy scenarios produce identical results."""
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      
      # Load legacy scenario
      config = load_scenario("scenarios/three_agent_barter.yaml")
      
      # Should have barter_only by default
      assert config.params.exchange_regime == "barter_only"
      
      # Run simulation
      sim = Simulation(config, seed=42, log_config=LogConfig.off())
      sim.run(max_ticks=10)
      
      # Verify agents have M=0
      for agent in sim.agents:
          assert agent.inventory.M == 0
          assert agent.lambda_money == 1.0
      
      # No trades should involve money
      # (Phase 1 doesn't change trade logic, so this is trivially true)
  ```

- [ ] **Test: Telemetry records barter_only correctly**
  ```python
  def test_telemetry_barter_only():
      """Verify telemetry records barter-only regime."""
      from vmt_engine.simulation import Simulation
      from scenarios.loader import load_scenario
      from telemetry.config import LogConfig
      import tempfile
      import sqlite3
      
      with tempfile.TemporaryDirectory() as tmpdir:
          db_path = f"{tmpdir}/test.db"
          config = load_scenario("scenarios/three_agent_barter.yaml")
          log_cfg = LogConfig(use_database=True, db_path=db_path)
          
          sim = Simulation(config, seed=42, log_config=log_cfg)
          sim.run(max_ticks=5)
          sim.close()
          
          # Query tick_states
          conn = sqlite3.connect(db_path)
          cursor = conn.execute("SELECT DISTINCT exchange_regime FROM tick_states")
          regimes = [row[0] for row in cursor.fetchall()]
          assert regimes == ["barter_only"]
          conn.close()
  ```

### 5.3) Snapshot comparison test

- [ ] **Create snapshot comparison script**
  ```bash
  # scripts/compare_telemetry_snapshots.py
  # Compare baseline_telemetry.db vs. new run
  # Verify agent positions, inventories (A,B), trades identical
  # Ignore new money columns (should be 0/NULL)
  ```

- [ ] **Run snapshot comparison**
  ```bash
  python scripts/compare_telemetry_snapshots.py baseline_telemetry.db logs/telemetry.db
  # Should report: "Identical behavior, new columns added"
  ```

---

## Part 6: Documentation and Cleanup

### 6.1) Update docstrings

- [ ] **Document money fields in schema.py**
  ```python
  # Add comprehensive docstrings to new fields explaining defaults
  ```

- [ ] **Document Inventory.M field**
  ```python
  @dataclass
  class Inventory:
      """Agent inventory state.
      
      Attributes:
          A: Quantity of good A (integer ≥ 0)
          B: Quantity of good B (integer ≥ 0)
          M: Money holdings in minor units (integer ≥ 0, Phase 1+)
      """
      A: int = 0
      B: int = 0
      M: int = 0
  ```

- [ ] **Update Simulation class docstring**
  ```python
  # Mention money system in initialization, note Phase 1 just adds state
  ```

### 6.2) Update type hints

- [ ] **Verify all money params have proper type hints**
- [ ] **Run mypy if configured**
  ```bash
  mypy src/vmt_engine src/scenarios src/telemetry
  ```

### 6.3) Code review prep

- [ ] **Self-review checklist**:
  - [ ] No logic changes to existing systems
  - [ ] All defaults preserve legacy behavior
  - [ ] New fields documented
  - [ ] Tests pass
  - [ ] No performance regressions

---

## Part 7: Final Verification

### 7.1) Run full test suite

- [ ] **Run all tests**
  ```bash
  pytest -v
  ```

- [ ] **Compare to baseline**
  ```bash
  diff baseline_tests.txt current_tests.txt
  # Should show only: new tests added, no failures
  ```

### 7.2) Run all example scenarios

- [ ] **Run each scenario in scenarios/ directory**
  ```bash
  for scenario in scenarios/*.yaml; do
      echo "Testing $scenario"
      python main.py "$scenario" --seed 42 > /dev/null || echo "FAILED: $scenario"
  done
  ```

- [ ] **Verify GUI launcher still works**
  ```bash
  python launcher.py
  # Manually verify scenario builder loads, no errors
  ```

### 7.3) Performance check

- [ ] **Run performance comparison**
  ```bash
  # Time a large scenario before and after
  time python main.py scenarios/large_scenario.yaml --seed 42
  # Should be within 5% of baseline
  ```

### 7.4) Database migration test

- [ ] **Test that old databases still open**
  ```bash
  python view_logs.py
  # Open baseline_telemetry.db (pre-Phase 1)
  # Verify viewer doesn't crash, just shows NULL for money columns
  ```

---

## Completion Criteria

**Phase 1 is complete when**:

✅ All new fields added to schema with backward-compatible defaults
✅ M inventory field exists but all legacy scenarios have M=0
✅ Telemetry database includes money columns (NULL/0 in legacy runs)
✅ All existing tests pass unchanged
✅ Legacy scenarios produce identical behavior (verified by snapshot comparison)
✅ Code review approved
✅ Documentation updated

**Ready for Phase 2 when**:
- Can create a scenario with `initial_inventories.M = 100` without errors
- Can set `exchange_regime = "money_only"` without errors (won't enforce yet)
- Telemetry logs `tick_states` with exchange_regime field

---

## Rollback Plan

If Phase 1 causes issues:

1. Revert branch: `git checkout main`
2. Investigate failures in feature branch
3. Fix issues, re-test
4. Do NOT merge until 100% behavior preservation verified

---

## Notes

- **No shortcuts**: Phase 1 must be perfect. All future phases depend on this foundation.
- **Test extensively**: Every existing scenario must work identically.
- **Document everything**: Future developers need to understand why defaults are chosen.

**Estimated effort**: 6-8 hours for experienced developer familiar with codebase.

---

See also:
- `money_SSOT_implementation_plan.md` — Overall strategy
- `money_telemetry_schema.md` — Database schema details
- `docs/4_typing_overview.md` — Type contracts

