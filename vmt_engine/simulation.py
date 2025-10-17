"""
Main simulation loop and orchestration.
"""

import numpy as np
from typing import Optional
from .core import Grid, Agent, Inventory, Position, SpatialIndex
from scenarios.schema import ScenarioConfig
from .econ.utility import create_utility
from .systems.perception import perceive
from .systems.movement import choose_forage_target, next_step_toward
from .systems.foraging import forage
from .systems.quotes import compute_quotes, refresh_quotes_if_needed
from .systems.matching import choose_partner, trade_pair

# New database-backed logging
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
        """Execute one simulation tick."""
        self.perception_phase()
        self.decision_phase()
        self.movement_phase()
        self.trade_phase()
        self.forage_phase()
        self.resource_regeneration_phase()
        self.housekeeping_phase()
        self.tick += 1
    
    def perception_phase(self):
        """Phase 1: Agents perceive their environment."""
        for agent in self.agents:
            # Use spatial index to find nearby agents efficiently (O(N) instead of O(N²))
            nearby_agent_ids = self.spatial_index.query_radius(
                agent.pos, 
                agent.vision_radius, 
                exclude_id=agent.id
            )
            
            perception = perceive(agent, self.grid, nearby_agent_ids, self.agent_by_id)
            agent.perception_cache = {
                'neighbors': perception.neighbors,
                'neighbor_quotes': perception.neighbor_quotes,
                'resource_cells': perception.resource_cells
            }
    
    def decision_phase(self):
        """Phase 2: Agents make decisions about targets."""
        for agent in self.agents:
            # Try to find a trading partner first
            neighbors = agent.perception_cache.get('neighbors', [])
            partner_id, surplus, all_candidates = choose_partner(agent, neighbors, self.agent_by_id, self.tick)

            if partner_id is not None:
                # Move toward partner
                partner = self.agent_by_id[partner_id]
                agent.target_pos = partner.pos
                agent.target_agent_id = partner_id
                
                # Log decision
                alternatives_str = "; ".join([f"{nid}:{s:.4f}" for nid, s in all_candidates])
                self.telemetry.log_decision(
                    self.tick, agent.id, partner_id, surplus,
                    "trade", partner.pos[0], partner.pos[1],
                    len(neighbors), alternatives_str
                )
            else:
                # Fall back to foraging
                resource_cells = agent.perception_cache.get('resource_cells', [])
                target = choose_forage_target(agent, resource_cells, self.params['beta'],
                                              self.params['forage_rate'])
                agent.target_pos = target
                agent.target_agent_id = None
                
                # Log decision
                target_type = "forage" if target is not None else "idle"
                target_x = target[0] if target is not None else None
                target_y = target[1] if target is not None else None
                alternatives_str = "; ".join([f"{nid}:{s:.4f}" for nid, s in all_candidates])
                self.telemetry.log_decision(
                    self.tick, agent.id, None, None,
                    target_type, target_x, target_y,
                    len(neighbors), alternatives_str
                )

    def movement_phase(self):
        """Phase 3: Agents move toward targets."""
        for agent in self.agents:
            if agent.target_pos is not None:
                # If targeting an agent, check if already in interaction range.
                if agent.target_agent_id is not None:
                    target_agent = self.agent_by_id.get(agent.target_agent_id)
                    if target_agent:
                        distance = self.grid.manhattan_distance(agent.pos, target_agent.pos)
                        if distance <= self.params['interaction_radius']:
                            continue  # Already in range, don't move.

                # Check for diagonal deadlock with another agent
                if agent.target_agent_id is not None:
                    target_agent = self.agent_by_id.get(agent.target_agent_id)
                    if target_agent and target_agent.target_agent_id == agent.id:
                        # Both agents are targeting each other.
                        # Check if they are diagonally adjacent
                        if self.grid.manhattan_distance(agent.pos, target_agent.pos) == 2 and \
                           abs(agent.pos[0] - target_agent.pos[0]) == 1 and \
                           abs(agent.pos[1] - target_agent.pos[1]) == 1:
                            # Diagonal deadlock detected. Only higher ID agent moves.
                            if agent.id < target_agent.id:
                                continue  # Lower ID agent waits

                new_pos = next_step_toward(
                    agent.pos,
                    agent.target_pos,
                    self.params['move_budget_per_tick']
                )
                agent.pos = new_pos
                # Update spatial index with new position
                self.spatial_index.update_position(agent.id, new_pos)
    
    def trade_phase(self):
        """Phase 4: Agents trade with nearby partners."""
        # Use spatial index to find agent pairs within interaction_radius efficiently
        # O(N) instead of O(N²) by only checking agents in nearby spatial buckets
        pairs = self.spatial_index.query_pairs_within_radius(self.params['interaction_radius'])
        
        # Sort pairs by (min_id, max_id) for deterministic processing
        pairs.sort()
        
        # Execute trades
        for id_i, id_j in pairs:
            agent_i = self.agent_by_id[id_i]
            agent_j = self.agent_by_id[id_j]
            
            trade_pair(agent_i, agent_j, self.params, self.telemetry, self.tick)
    
    def forage_phase(self):
        """Phase 5: Agents harvest resources."""
        for agent in self.agents:
            forage(agent, self.grid, self.params['forage_rate'], self.tick)
    
    def resource_regeneration_phase(self):
        """Phase 6: Resources regenerate after cooldown period."""
        from .systems.foraging import regenerate_resources
        regenerate_resources(
            self.grid,
            self.params['resource_growth_rate'],
            self.params['resource_max_amount'],
            self.params['resource_regen_cooldown'],
            self.tick
        )
    
    def housekeeping_phase(self):
        """Phase 7: Update quotes, log telemetry, cleanup."""
        # Refresh quotes for agents whose inventory changed
        for agent in self.agents:
            refresh_quotes_if_needed(agent, self.params['spread'], self.params['epsilon'])
        
        # Log telemetry
        self.telemetry.log_agent_snapshots(self.tick, self.agents)
        self.telemetry.log_resource_snapshots(self.tick, self.grid)
    
    def close(self):
        """Close all loggers and release resources."""
        if self.telemetry:
            self.telemetry.close()

