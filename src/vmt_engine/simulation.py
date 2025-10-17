"""
Main simulation loop and orchestration.
"""

import numpy as np
from typing import Optional
from .core import Grid, Agent, Inventory, SpatialIndex
from scenarios.schema import ScenarioConfig
from .econ.utility import create_utility
from .systems.perception import PerceptionSystem
from .systems.movement import MovementSystem
from .systems.foraging import ForageSystem, ResourceRegenerationSystem
from .systems.quotes import compute_quotes
from .systems.decision import DecisionSystem
from .systems.trading import TradeSystem
from .systems.housekeeping import HousekeepingSystem

# Database-backed telemetry
from telemetry import TelemetryManager, LogConfig


class Simulation:
    """Main simulation class coordinating all phases."""
    
    def __init__(self, scenario_config: ScenarioConfig, seed: int, 
                 log_config: Optional[LogConfig] = None):
        """
        Initialize simulation from scenario configuration.
        
        Args:
            scenario_config: Loaded and validated scenario
            seed: Random seed for reproducibility
            log_config: Configuration for new database logging system (optional)
        """
        self.config = scenario_config
        self.seed = seed
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Simulation state - initialize params first
        self.tick = 0
        self.params = {
            'spread': scenario_config.params.spread,
            'vision_radius': scenario_config.params.vision_radius,
            'interaction_radius': scenario_config.params.interaction_radius,
            'move_budget_per_tick': scenario_config.params.move_budget_per_tick,
            'dA_max': scenario_config.params.dA_max,
            'forage_rate': scenario_config.params.forage_rate,
            'epsilon': scenario_config.params.epsilon,
            'beta': scenario_config.params.beta,
            'resource_growth_rate': scenario_config.params.resource_growth_rate,
            'resource_max_amount': scenario_config.params.resource_max_amount,
            'resource_regen_cooldown': scenario_config.params.resource_regen_cooldown,
            'trade_cooldown_ticks': scenario_config.params.trade_cooldown_ticks,
        }
        
        # Initialize systems in the correct tick order
        self.systems = [
            PerceptionSystem(),
            DecisionSystem(),
            MovementSystem(),
            TradeSystem(),
            ForageSystem(),
            ResourceRegenerationSystem(),
            HousekeepingSystem(),
        ]
        
        # Initialize grid
        self.grid = Grid(scenario_config.N)
        self.grid.seed_resources(
            self.rng, 
            scenario_config.resource_seed.density,
            scenario_config.resource_seed.amount
        )
        
        # Initialize agents
        self.agents: list[Agent] = []
        self.agent_by_id: dict[int, Agent] = {}
        self._initialize_agents()
        
        # Sort agents by id for deterministic processing
        self.agents.sort(key=lambda a: a.id)
        
        # Initialize spatial index for efficient proximity queries
        # Bucket size = max query radius for optimal performance
        max_radius = max(self.params['vision_radius'], self.params['interaction_radius'])
        self.spatial_index = SpatialIndex(self.config.N, bucket_size=max_radius)
        for agent in self.agents:
            self.spatial_index.add_agent(agent.id, agent.pos)
        
        # Telemetry
        if log_config is None:
            log_config = LogConfig.standard()  # Default to standard logging
        
        self.telemetry = TelemetryManager(log_config, scenario_name=scenario_config.name or "simulation")
        self.telemetry.start_run(
            num_agents=len(self.agents),
            grid_width=self.config.N,
            grid_height=self.config.N,
            config_dict={'seed': seed, 'params': self.params}
        )
    
    def _initialize_agents(self):
        """Initialize agents from scenario config."""
        n_agents = self.config.agents
        
        # Parse initial inventories
        inv_A = self.config.initial_inventories['A']
        inv_B = self.config.initial_inventories['B']
        
        # Convert to lists if needed
        if isinstance(inv_A, int):
            inv_A = [inv_A] * n_agents
        if isinstance(inv_B, int):
            inv_B = [inv_B] * n_agents
        
        if len(inv_A) != n_agents or len(inv_B) != n_agents:
            raise ValueError(f"Initial inventory lists must match agent count {n_agents}")
        
        # Sample utility types according to mix weights
        utility_configs = []
        weights = [u.weight for u in self.config.utilities.mix]
        
        for i in range(n_agents):
            # Sample utility type according to weights
            util_choice = self.rng.choice(len(self.config.utilities.mix), p=weights)
            util_config = self.config.utilities.mix[util_choice]
            utility_configs.append(util_config)
        
        # Create agents with random positions
        for i in range(n_agents):
            x = self.rng.integers(0, self.config.N)
            y = self.rng.integers(0, self.config.N)
            pos = (x, y)
            
            inventory = Inventory(A=inv_A[i], B=inv_B[i])
            
            # Create utility
            utility = create_utility({
                'type': utility_configs[i].type,
                'params': utility_configs[i].params
            })
            
            agent = Agent(
                id=i,
                pos=pos,
                inventory=inventory,
                utility=utility,
                vision_radius=self.params['vision_radius'],
                move_budget_per_tick=self.params['move_budget_per_tick']
            )
            
            # Initialize quotes
            agent.quotes = compute_quotes(agent, self.params['spread'], self.params['epsilon'])
            agent.inventory_changed = False
            
            self.agents.append(agent)
            self.agent_by_id[i] = agent
    
    def run(self, max_ticks: int):
        """
        Run simulation for specified number of ticks.
        
        Args:
            max_ticks: Number of ticks to simulate
        """
        for _ in range(max_ticks):
            self.step()
        
        # Finalize logging
        if self.telemetry:
            self.telemetry.finalize_run(max_ticks)
    
    def step(self):
        """Execute one simulation tick by running each system in order.
        
        7-phase tick order (see PLANS/Planning-Post-v1.md):
        1. Perception → 2. Decision → 3. Movement → 4. Trade → 
        5. Forage → 6. Resource Regeneration → 7. Housekeeping
        """
        for system in self.systems:
            system.execute(self)
        self.tick += 1
    
    def close(self):
        """Close all loggers and release resources."""
        if self.telemetry:
            self.telemetry.close()

