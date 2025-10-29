"""
Test market clearing inventory safety to prevent negative inventories.

This test verifies that the Walrasian market clearing mechanism never
causes negative inventories, even in complex scenarios with multiple
commodities and multiple trades per agent.
"""

import pytest
from vmt_engine.simulation import Simulation
from vmt_engine.core import Agent, Inventory, Position
from vmt_engine.econ.utility import UCES
from scenarios.loader import load_scenario


def test_market_clearing_inventory_safety():
    """Test that market clearing never causes negative inventories."""
    # Create a simple scenario that forces market formation
    scenario = load_scenario("scenarios/demos/emergent_market_basic.yaml")
    
    # Run simulation for a few ticks to let markets form
    sim = Simulation(scenario, seed=42)
    
    # Step through simulation and check inventories after each step
    for tick in range(50):
        # Store inventories before step
        pre_inventories = {}
        for agent in sim.agents:
            pre_inventories[agent.id] = {
                'A': agent.inventory.A,
                'B': agent.inventory.B,
                'M': agent.inventory.M
            }
        
        # Take step
        sim.step()
        
        # Check inventories after step
        for agent in sim.agents:
            assert agent.inventory.A >= 0, f"Agent {agent.id} A inventory negative: {agent.inventory.A} at tick {tick}"
            assert agent.inventory.B >= 0, f"Agent {agent.id} B inventory negative: {agent.inventory.B} at tick {tick}"
            assert agent.inventory.M >= 0, f"Agent {agent.id} M inventory negative: {agent.inventory.M} at tick {tick}"
            
            # Also check that inventories changed reasonably (not too dramatically)
            pre_inv = pre_inventories[agent.id]
            delta_A = agent.inventory.A - pre_inv['A']
            delta_B = agent.inventory.B - pre_inv['B']
            delta_M = agent.inventory.M - pre_inv['M']
            
            # Inventories shouldn't change by more than 50 units in a single tick
            assert abs(delta_A) <= 50, f"Agent {agent.id} A inventory changed too much: {delta_A} at tick {tick}"
            assert abs(delta_B) <= 50, f"Agent {agent.id} B inventory changed too much: {delta_B} at tick {tick}"
            assert abs(delta_M) <= 50, f"Agent {agent.id} M inventory changed too much: {delta_M} at tick {tick}"
    
    sim.close()


def test_market_clearing_with_multiple_commodities():
    """Test market clearing when agents trade both A and B commodities."""
    # Create a scenario that forces both A and B trading
    scenario = load_scenario("scenarios/demos/emergent_market_multi.yaml")
    
    # Run simulation and check for negative inventories
    sim = Simulation(scenario, seed=42)
    
    try:
        for tick in range(100):  # Longer run to catch the issue
            sim.step()
            
            # Check all agent inventories
            for agent in sim.agents:
                assert agent.inventory.A >= 0, f"Agent {agent.id} A inventory negative: {agent.inventory.A} at tick {tick}"
                assert agent.inventory.B >= 0, f"Agent {agent.id} B inventory negative: {agent.inventory.B} at tick {tick}"
                assert agent.inventory.M >= 0, f"Agent {agent.id} M inventory negative: {agent.inventory.M} at tick {tick}"
                
    except AssertionError as e:
        # Print debug information
        print(f"\nNegative inventory detected at tick {sim.tick}")
        print("Agent inventories:")
        for agent in sim.agents:
            print(f"  Agent {agent.id}: A={agent.inventory.A}, B={agent.inventory.B}, M={agent.inventory.M}")
        
        # Print market information
        if hasattr(sim, 'trade_system') and hasattr(sim.trade_system, 'active_markets'):
            print("Active markets:")
            for market in sim.trade_system.active_markets.values():
                print(f"  Market {market.id}: participants={market.participant_ids}, prices={market.current_prices}")
        
        raise e
    
    finally:
        sim.close()


if __name__ == "__main__":
    test_market_clearing_inventory_safety()
    test_market_clearing_with_multiple_commodities()
