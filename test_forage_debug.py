"""Quick debug of single agent forage issue."""

from src.scenarios.loader import load_scenario
from src.vmt_engine.simulation import Simulation

scenario = load_scenario("scenarios/single_agent_forage.yaml")
sim = Simulation(scenario, seed=42)

agent = sim.agents[0]
print(f"Initial state:")
print(f"  Agent pos: {agent.pos}")
print(f"  Agent inv: A={agent.inventory.A}, B={agent.inventory.B}")
print(f"  Resources on grid: {sum(1 for cell in sim.grid.cells if cell.resource is not None)}")
print(f"  Mode: {sim.current_mode}")
print(f"  Search protocol: {sim.search_protocol}")
print(f"  Decision system has protocol: {sim.systems[1].search_protocol}")

# Run a few ticks with detailed output
for tick in range(5):
    print(f"\n--- Tick {tick} ---")
    
    # Run tick
    sim.step()
    
    # Check agent state
    print(f"  After tick: pos={agent.pos}, inv_A={agent.inventory.A}, inv_B={agent.inventory.B}")
    print(f"  Target: {agent.target_pos}, type={getattr(agent, '_decision_target_type', None)}")
    print(f"  Resources visible in perception: {len(agent.perception_cache.get('resource_cells', []))}")
    
    # Check if agent is on a resource
    cell = sim.grid.get_cell(agent.pos[0], agent.pos[1])
    if cell.resource is not None:
        print(f"  Agent ON resource: type={cell.resource.type}, amount={cell.resource.amount}")
    else:
        print(f"  Agent NOT on resource")

print(f"\nFinal inventory: A={agent.inventory.A}, B={agent.inventory.B}")
print(f"Total harvested: {agent.inventory.A + agent.inventory.B}")

