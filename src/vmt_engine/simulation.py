"""
Main simulation loop and orchestration.
"""

import numpy as np
from typing import Optional
from decimal import Decimal
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

# Protocol system - fully implemented and configurable via scenario_config
# from .protocols import SearchProtocol, MatchingProtocol, BargainingProtocol


class Simulation:
    """Main simulation class coordinating all phases."""
    
    def __init__(self, scenario_config: ScenarioConfig, seed: int, 
                 log_config: Optional[LogConfig] = None,
                 search_protocol: Optional["SearchProtocol"] = None,
                 matching_protocol: Optional["MatchingProtocol"] = None,
                 bargaining_protocol: Optional["BargainingProtocol"] = None):
        """
        Initialize simulation from scenario configuration.
        
        Args:
            scenario_config: Loaded and validated scenario
            seed: Random seed for reproducibility
            log_config: Configuration for new database logging system (optional)
            search_protocol: Optional search protocol (CLI override)
            matching_protocol: Optional matching protocol (CLI override)
            bargaining_protocol: Optional bargaining protocol (CLI override)
        
        Protocol Resolution Order:
            1. CLI argument (if provided) - overrides everything
            2. Scenario YAML configuration (if specified)
            3. Legacy defaults (fallback)
        """
        self.config = scenario_config
        self.seed = seed
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Protocol system with YAML configuration support
        # CLI arguments override YAML config, which overrides legacy defaults
        from scenarios.protocol_factory import (
            get_search_protocol,
            get_matching_protocol,
            get_bargaining_protocol
        )
        
        # Search protocol: CLI > YAML > legacy default
        if search_protocol is not None:
            self.search_protocol = search_protocol  # CLI override
        else:
            self.search_protocol = get_search_protocol(scenario_config.search_protocol)
        
        # Matching protocol: CLI > YAML > legacy default
        if matching_protocol is not None:
            self.matching_protocol = matching_protocol  # CLI override
        else:
            self.matching_protocol = get_matching_protocol(scenario_config.matching_protocol)
        
        # Bargaining protocol: CLI > YAML > legacy default
        if bargaining_protocol is not None:
            self.bargaining_protocol = bargaining_protocol  # CLI override
        else:
            self.bargaining_protocol = get_bargaining_protocol(scenario_config.bargaining_protocol)
        
        # Simulation state - initialize params first
        self.tick = 0
        self.params = {
            'spread': scenario_config.params.spread,
            'vision_radius': scenario_config.params.vision_radius,
            'interaction_radius': scenario_config.params.interaction_radius,
            'move_budget_per_tick': scenario_config.params.move_budget_per_tick,
            'forage_rate': scenario_config.params.forage_rate,
            'epsilon': scenario_config.params.epsilon,
            'beta': scenario_config.params.beta,
            'resource_growth_rate': scenario_config.params.resource_growth_rate,
            'resource_max_amount': scenario_config.params.resource_max_amount,
            'resource_regen_cooldown': scenario_config.params.resource_regen_cooldown,
            'trade_cooldown_ticks': scenario_config.params.trade_cooldown_ticks,
            # Resource claiming system parameters
            'enable_resource_claiming': scenario_config.params.enable_resource_claiming,
            'enforce_single_harvester': scenario_config.params.enforce_single_harvester,
            # Telemetry parameters
            'log_preferences': scenario_config.params.log_preferences,
        }
        
        # Mode tracking - initialize based on schedule if present
        if scenario_config.mode_schedule:
            self.current_mode: str = scenario_config.mode_schedule.get_mode_at_tick(0)
        else:
            self.current_mode: str = "both"
        self._previous_mode: Optional[str] = None
        self._mode_change_tick: Optional[int] = None
        
        # Initialize systems in the correct tick order
        # Create decision system and inject protocols
        decision_system = DecisionSystem()
        decision_system.search_protocol = self.search_protocol
        decision_system.matching_protocol = self.matching_protocol
        
        # Create trade system and inject bargaining protocol
        trade_system = TradeSystem()
        trade_system.bargaining_protocol = self.bargaining_protocol
        
        self.systems = [
            PerceptionSystem(),
            decision_system,
            MovementSystem(),
            trade_system,
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
        
        # Track initial state for post-run summaries
        from decimal import Decimal
        self._start_inventory: dict[int, dict[str, Decimal]] = {}
        self._start_utility: dict[int, Optional[float]] = {}
        self._gathered_resources: dict[int, dict[str, Decimal]] = {}
        self._trades_made: dict[int, int] = {}
        self._summary_printed = False

        for agent in self.agents:
            self._start_inventory[agent.id] = {
                "A": agent.inventory.A,  # Store as Decimal
                "B": agent.inventory.B,  # Store as Decimal
            }

            if agent.utility is not None:
                self._start_utility[agent.id] = float(agent.utility.u(agent.inventory.A, agent.inventory.B))
            else:
                self._start_utility[agent.id] = None

            self._gathered_resources[agent.id] = {"A": Decimal('0'), "B": Decimal('0')}
            self._trades_made[agent.id] = 0
        
        # Initialize spatial index for efficient proximity queries
        # Bucket size = max query radius for optimal performance
        max_radius = max(self.params['vision_radius'], self.params['interaction_radius'])
        self.spatial_index = SpatialIndex(self.config.N, bucket_size=max_radius)
        for agent in self.agents:
            self.spatial_index.add_agent(agent.id, agent.pos)
        
        # Resource claiming system
        self.resource_claims: dict[tuple[int, int], int] = {}  # position -> claiming_agent_id
        
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
        
        # Determine agent positions
        n_cells = self.config.N * self.config.N
        if n_agents <= n_cells:
            # Assign unique positions if possible
            all_positions = [(x, y) for x in range(self.config.N) for y in range(self.config.N)]
            self.rng.shuffle(all_positions)
            positions = all_positions[:n_agents]
        else:
            # Fallback to random placement if more agents than cells
            positions = [
                (self.rng.integers(0, self.config.N), self.rng.integers(0, self.config.N))
                for _ in range(n_agents)
            ]

        # Create agents
        for i in range(n_agents):
            pos = positions[i]
            
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
                move_budget_per_tick=self.params['move_budget_per_tick'],
                home_pos=pos  # Set home position to initial position
            )
            
            # Initialize quotes
            agent.quotes = compute_quotes(
                agent, 
                self.params['spread'], 
                self.params['epsilon']
            )
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
        """Execute one simulation tick with mode-aware phase execution.
        
        7-phase tick order:
        1. Perception → 2. Decision → 3. Movement → 4. Trade → 
        5. Forage → 6. Resource Regeneration → 7. Housekeeping
        """
        # Determine current mode
        if self.config.mode_schedule:
            new_mode = self.config.mode_schedule.get_mode_at_tick(self.tick)
            
            # Detect and log mode changes
            if new_mode != self.current_mode:
                self._handle_mode_transition(self.current_mode, new_mode)
                self.current_mode = new_mode
                self._mode_change_tick = self.tick
        else:
            self.current_mode = "both"
        
        # Execute systems conditionally based on mode
        for system in self.systems:
            if self._should_execute_system(system, self.current_mode):
                system.execute(self)
        
        # Log tick state for observability
        if self.telemetry:
            self.telemetry.log_tick_state(
                self.tick,
                self.current_mode
            )
        
        self.tick += 1
    
    def _should_execute_system(self, system, mode: str) -> bool:
        """Determine if a system should execute in the current mode."""
        from .systems.perception import PerceptionSystem
        from .systems.decision import DecisionSystem
        from .systems.movement import MovementSystem
        from .systems.foraging import ForageSystem, ResourceRegenerationSystem
        from .systems.trading import TradeSystem
        from .systems.housekeeping import HousekeepingSystem
        
        # Always execute core systems
        always_execute = (PerceptionSystem, DecisionSystem, MovementSystem, 
                         ResourceRegenerationSystem, HousekeepingSystem)
        
        if isinstance(system, always_execute):
            return True
        
        # Mode-specific systems
        if isinstance(system, TradeSystem):
            return mode in ["trade", "both"]
        
        if isinstance(system, ForageSystem):
            return mode in ["forage", "both"]
        
        return True
    
    def _handle_mode_transition(self, old_mode: str, new_mode: str):
        """Handle bookkeeping when modes change."""
        # Log the transition
        if self.telemetry:
            self.telemetry.log_mode_change(self.tick, old_mode, new_mode)
        
        # Clear all pairings when mode changes
        self._clear_pairings_on_mode_switch(old_mode, new_mode)
        
        # Clear all foraging commitments on mode change
        for agent in self.agents:
            if agent.is_foraging_committed:
                agent.is_foraging_committed = False
                agent.forage_target_pos = None
    
    def _clear_pairings_on_mode_switch(self, old_mode: str, new_mode: str) -> None:
        """Clear all pairings when mode changes."""
        if old_mode == new_mode:
            return
        
        # Log unpair events for all paired agents
        for agent in self.agents:
            if agent.paired_with_id is not None:
                # Only log once per pair (lower ID does it)
                if agent.id < agent.paired_with_id:
                    self.telemetry.log_pairing_event(
                        self.tick, agent.id, agent.paired_with_id,
                        "unpair", f"mode_switch_{old_mode}_to_{new_mode}"
                    )
                agent.paired_with_id = None
        
        # No cooldowns on mode-switch unpairings (can re-pair immediately)
    
    
    def print_summary(self) -> None:
        """Print per-agent post-simulation summary to stdout."""
        if getattr(self, "_summary_printed", False):
            return

        def fmt_decimal(value: Decimal) -> str:
            """Format Decimal value without trailing zeros."""
            s = f"{value:.10f}"
            if '.' in s:
                s = s.rstrip('0').rstrip('.')
            return s

        def fmt_signed_int(value: int) -> str:
            if value > 0:
                return f"+{value}"
            return str(value)

        def fmt_signed_float(value: float) -> str:
            if abs(value) < 1e-12:
                value = 0.0
            if value > 0:
                return f"+{value:.2f}"
            return f"{value:.2f}"

        print(f"\nPost-sim summary (ticks={self.tick})")

        for agent in sorted(self.agents, key=lambda a: a.id):
            start_inv = self._start_inventory.get(agent.id, {"A": Decimal('0'), "B": Decimal('0')})
            # Format end inventory as decimals without trailing zeros
            end_inv_A = fmt_decimal(agent.inventory.A)
            end_inv_B = fmt_decimal(agent.inventory.B)
            
            # Calculate deltas using Decimal values
            # Ensure start values are Decimal (convert if they were stored as int)
            start_A_dec = Decimal(str(start_inv["A"])) if not isinstance(start_inv["A"], Decimal) else start_inv["A"]
            start_B_dec = Decimal(str(start_inv["B"])) if not isinstance(start_inv["B"], Decimal) else start_inv["B"]
            delta_a_dec = agent.inventory.A - start_A_dec
            delta_b_dec = agent.inventory.B - start_B_dec
            delta_a = fmt_decimal(delta_a_dec)
            delta_b = fmt_decimal(delta_b_dec)

            start_util = self._start_utility.get(agent.id)
            end_util: Optional[float] = None
            if agent.utility is not None:
                end_util = float(agent.utility.u(agent.inventory.A, agent.inventory.B))

            if start_util is not None and end_util is not None:
                util_segment = (
                    f"U {start_util:.2f}->{end_util:.2f} "
                    f"(d {fmt_signed_float(end_util - start_util)})"
                )
            elif end_util is not None:
                util_segment = f"U n/a->{end_util:.2f}"
            else:
                util_segment = "U n/a"

            gathered = self._gathered_resources.get(agent.id, {"A": Decimal('0'), "B": Decimal('0')})
            trades = self._trades_made.get(agent.id, 0)

            # Format start inventory for display
            start_A_str = fmt_decimal(start_A_dec)
            start_B_str = fmt_decimal(start_B_dec)
            
            # Format delta with sign
            delta_a_signed = f"+{delta_a}" if delta_a_dec >= 0 else delta_a
            delta_b_signed = f"+{delta_b}" if delta_b_dec >= 0 else delta_b
            
            inventory_segment = (
                f"A {start_A_str}->{end_inv_A} (d {delta_a_signed}), "
                f"B {start_B_str}->{end_inv_B} (d {delta_b_signed})"
            )

            gathered_A = fmt_decimal(gathered.get('A', Decimal('0')))
            gathered_B = fmt_decimal(gathered.get('B', Decimal('0')))
            gathered_segment = f"gathered A:{gathered_A} B:{gathered_B}"

            if agent.utility is not None:
                utility_label = agent.utility.__class__.__name__
            else:
                utility_label = "None"

            print(
                f"Agent {agent.id} ({utility_label}): {inventory_segment} | {util_segment} | "
                f"{gathered_segment} | trades: {trades}"
            )

        self._summary_printed = True

    def close(self):
        """Close all loggers and release resources."""
        self.print_summary()

        if self.telemetry:
            self.telemetry.close()

