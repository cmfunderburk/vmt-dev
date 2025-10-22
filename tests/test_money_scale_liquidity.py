"""
Test that money_scale properly scales initial money inventories for liquidity.
"""
import pytest
from scenarios.loader import load_scenario
from vmt_engine.simulation import Simulation


def test_money_scale_multiplies_initial_inventory():
    """Verify that money_scale directly multiplies initial M inventory values."""
    # Create a simple test scenario
    import yaml
    import tempfile
    import os
    
    scenario_yaml = """
schema_version: 1
name: test_money_scale
N: 10
agents: 3

initial_inventories:
  A: [10, 20, 30]
  B: [10, 20, 30]
  M: [100, 200, 300]

utilities:
  mix:
    - type: linear
      weight: 1.0
      params:
        vA: 1.0
        vB: 1.0

params:
  exchange_regime: money_only
  money_mode: quasilinear
  money_scale: 1000  # 1000x multiplier
  lambda_money: 1.0

resource_seed:
  density: 0.0
  amount: 0
"""
    
    # Write to temp file and load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(scenario_yaml)
        temp_path = f.name
    
    try:
        scenario = load_scenario(temp_path)
        sim = Simulation(scenario, seed=42)
        
        # Verify agents have scaled money inventories
        assert sim.agents[0].inventory.M == 100 * 1000  # 100,000
        assert sim.agents[1].inventory.M == 200 * 1000  # 200,000
        assert sim.agents[2].inventory.M == 300 * 1000  # 300,000
        
        # Verify A and B inventories are NOT scaled
        assert sim.agents[0].inventory.A == 10
        assert sim.agents[1].inventory.A == 20
        assert sim.agents[2].inventory.A == 30
        
        assert sim.agents[0].inventory.B == 10
        assert sim.agents[1].inventory.B == 20
        assert sim.agents[2].inventory.B == 30
        
    finally:
        os.unlink(temp_path)


def test_money_scale_1_no_multiplier():
    """Verify that money_scale=1 leaves M inventory unchanged."""
    import yaml
    import tempfile
    import os
    
    scenario_yaml = """
schema_version: 1
name: test_money_scale_1
N: 10
agents: 2

initial_inventories:
  A: 10
  B: 10
  M: 50

utilities:
  mix:
    - type: linear
      weight: 1.0
      params:
        vA: 1.0
        vB: 1.0

params:
  exchange_regime: money_only
  money_mode: quasilinear
  money_scale: 1  # No multiplier
  lambda_money: 1.0

resource_seed:
  density: 0.0
  amount: 0
"""
    
    # Write to temp file and load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(scenario_yaml)
        temp_path = f.name
    
    try:
        scenario = load_scenario(temp_path)
        sim = Simulation(scenario, seed=42)
        
        # Verify agents have original M inventory (50 * 1 = 50)
        assert sim.agents[0].inventory.M == 50
        assert sim.agents[1].inventory.M == 50
        
    finally:
        os.unlink(temp_path)


def test_money_scale_proportional_liquidity():
    """
    Verify that money_scale scales both M inventory and prices proportionally.
    
    This maintains constant purchasing power (M / prices), which is the 
    intended liquidity behavior.
    """
    import yaml
    import tempfile
    import os
    
    scenario_template = """
schema_version: 1
name: test_money_scale_liquidity
N: 10
agents: 2

initial_inventories:
  A: [10, 0]
  B: [0, 10]
  M: [100, 100]

utilities:
  mix:
    - type: linear
      weight: 1.0
      params:
        vA: 2.0
        vB: 1.0

params:
  exchange_regime: money_only
  money_mode: quasilinear
  money_scale: {money_scale}
  lambda_money: 1.0

resource_seed:
  density: 0.0
  amount: 0
"""
    
    results = {}
    
    # Test with two different scales
    for scale in [1, 100]:
        scenario_yaml = scenario_template.format(money_scale=scale)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(scenario_yaml)
            temp_path = f.name
        
        try:
            scenario = load_scenario(temp_path)
            sim = Simulation(scenario, seed=42)
            
            # Verify M inventory scaled correctly
            assert sim.agents[0].inventory.M == 100 * scale
            assert sim.agents[1].inventory.M == 100 * scale
            
            # Store price for comparison
            results[scale] = {
                'M': sim.agents[0].inventory.M,
                'price': sim.agents[0].quotes['ask_A_in_M']
            }
            
        finally:
            os.unlink(temp_path)
    
    # Verify both M and prices scaled by the same factor (100x)
    # This maintains purchasing power: (M / price) should be constant
    scale_ratio = results[100]['M'] / results[1]['M']
    price_ratio = results[100]['price'] / results[1]['price']
    
    assert scale_ratio == 100.0  # M scaled by 100x
    assert abs(price_ratio - 100.0) < 1.0  # Prices also scaled ~100x
    
    # Verify purchasing power is approximately constant
    purchasing_power_1 = results[1]['M'] / results[1]['price']
    purchasing_power_100 = results[100]['M'] / results[100]['price']
    
    # Allow small floating point tolerance
    assert abs(purchasing_power_1 - purchasing_power_100) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

