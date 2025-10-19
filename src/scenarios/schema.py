"""
Scenario schema definitions and validation.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from enum import Enum


@dataclass
class UtilityConfig:
    """Configuration for a utility function."""
    type: Literal["ces", "linear"]
    weight: float
    params: dict[str, float]


@dataclass
class UtilitiesMix:
    """Mix of utility functions."""
    mix: list[UtilityConfig]


@dataclass
class ResourceSeed:
    """Resource seeding configuration."""
    density: float
    amount: int | dict[str, Any]  # Can be int or distribution spec


class ModeType(str, Enum):
    """Types of mode scheduling patterns."""
    GLOBAL_CYCLE = "global_cycle"
    AGENT_SPECIFIC = "agent_specific"  # Future
    SPATIAL_ZONES = "spatial_zones"    # Future


@dataclass
class ModeSchedule:
    """Configuration for alternating phase modes."""
    type: Literal["global_cycle", "agent_specific", "spatial_zones"]
    forage_ticks: int
    trade_ticks: int
    start_mode: Literal["forage", "trade"] = "forage"
    
    def validate(self) -> None:
        """Validate mode schedule parameters."""
        if self.forage_ticks <= 0:
            raise ValueError(f"forage_ticks must be positive, got {self.forage_ticks}")
        if self.trade_ticks <= 0:
            raise ValueError(f"trade_ticks must be positive, got {self.trade_ticks}")
        if self.type != "global_cycle":
            raise NotImplementedError(f"Mode type {self.type} not yet implemented")
    
    def get_mode_at_tick(self, tick: int) -> Literal["forage", "trade", "both"]:
        """Determine the mode for a given tick."""
        if self.type == "global_cycle":
            cycle_length = self.forage_ticks + self.trade_ticks
            position_in_cycle = tick % cycle_length
            
            if self.start_mode == "forage":
                return "forage" if position_in_cycle < self.forage_ticks else "trade"
            else:
                return "trade" if position_in_cycle < self.trade_ticks else "forage"
        return "both"


@dataclass
class ScenarioParams:
    """Simulation parameters."""
    spread: float = 0.0
    vision_radius: int = 5
    interaction_radius: int = 1
    move_budget_per_tick: int = 1
    dA_max: int = 5  # Maximum trade size to search (formerly ΔA_max)
    forage_rate: int = 1
    epsilon: float = 1e-12
    beta: float = 0.95
    resource_growth_rate: int = 0          # Units that regenerate per tick (0 = no regen)
    resource_max_amount: int = 5           # Maximum resource amount per cell
    resource_regen_cooldown: int = 5       # Ticks to wait after depletion before regen starts
    trade_cooldown_ticks: int = 5          # Ticks to wait after failed trade before re-attempting same partner


@dataclass
class ScenarioConfig:
    """Complete scenario configuration."""
    schema_version: int
    name: str
    N: int  # Grid size (NxN)
    agents: int
    initial_inventories: dict[str, int | list[int]]
    utilities: UtilitiesMix
    params: ScenarioParams
    resource_seed: ResourceSeed
    mode_schedule: Optional[ModeSchedule] = None
    
    def validate(self) -> None:
        """Validate scenario parameters."""
        # Grid size
        if self.N <= 0:
            raise ValueError(f"Grid size N must be positive, got {self.N}")
        
        # Agent count
        if self.agents <= 0:
            raise ValueError(f"Agent count must be positive, got {self.agents}")
        
        # Params validation
        if self.params.spread < 0:
            raise ValueError(f"spread must be non-negative, got {self.params.spread}")
        
        if self.params.vision_radius < 0:
            raise ValueError(f"vision_radius must be non-negative, got {self.params.vision_radius}")
        
        if self.params.interaction_radius < 0:
            raise ValueError(f"interaction_radius must be non-negative, got {self.params.interaction_radius}")
        
        if self.params.move_budget_per_tick <= 0:
            raise ValueError(f"move_budget_per_tick must be positive, got {self.params.move_budget_per_tick}")
        
        if self.params.dA_max <= 0:
            raise ValueError(f"dA_max must be positive, got {self.params.dA_max}")
        
        if self.params.forage_rate <= 0:
            raise ValueError(f"forage_rate must be positive, got {self.params.forage_rate}")
        
        if self.params.epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {self.params.epsilon}")
        
        if not 0 < self.params.beta <= 1:
            raise ValueError(f"beta must be in (0, 1], got {self.params.beta}")
        
        if self.params.resource_growth_rate < 0:
            raise ValueError(f"resource_growth_rate must be non-negative, got {self.params.resource_growth_rate}")
        
        if self.params.resource_max_amount <= 0:
            raise ValueError(f"resource_max_amount must be positive, got {self.params.resource_max_amount}")
        
        if self.params.resource_regen_cooldown < 0:
            raise ValueError(f"resource_regen_cooldown must be non-negative, got {self.params.resource_regen_cooldown}")
        
        if self.params.trade_cooldown_ticks < 0:
            raise ValueError(f"trade_cooldown_ticks must be non-negative, got {self.params.trade_cooldown_ticks}")
        
        # Resource seed validation
        if not 0 <= self.resource_seed.density <= 1:
            raise ValueError(f"resource density must be in [0, 1], got {self.resource_seed.density}")
        
        # Utility mix validation
        if not self.utilities.mix:
            raise ValueError("utilities.mix must contain at least one utility function")
        
        total_weight = sum(u.weight for u in self.utilities.mix)
        if not abs(total_weight - 1.0) < 1e-6:
            raise ValueError(f"utility weights must sum to 1.0, got {total_weight}")
        
        # Validate each utility config
        for util in self.utilities.mix:
            if util.weight < 0:
                raise ValueError(f"utility weight must be non-negative, got {util.weight}")
            
            if util.type == "ces":
                if "rho" not in util.params:
                    raise ValueError("CES utility requires 'rho' parameter")
                if "wA" not in util.params or "wB" not in util.params:
                    raise ValueError("CES utility requires 'wA' and 'wB' parameters")
                if util.params["rho"] == 1.0:
                    raise ValueError("CES utility cannot have rho=1.0")
                if util.params["wA"] <= 0 or util.params["wB"] <= 0:
                    raise ValueError("CES weights must be positive")
            
            elif util.type == "linear":
                if "vA" not in util.params or "vB" not in util.params:
                    raise ValueError("Linear utility requires 'vA' and 'vB' parameters")
                if util.params["vA"] <= 0 or util.params["vB"] <= 0:
                    raise ValueError("Linear utility values must be positive")
        
        # Validate mode schedule if present
        if self.mode_schedule:
            self.mode_schedule.validate()

