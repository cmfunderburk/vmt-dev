"""
Scenario schema definitions and validation.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from enum import Enum


@dataclass
class UtilityConfig:
    """Configuration for a utility function."""
    type: Literal["ces", "linear", "quadratic", "translog", "stone_geary"]
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
    
    # --- Trade execution parameters ---
    trade_execution_mode: Literal["minimum", "maximum"] = "minimum"
    """
    Controls how trade quantities are determined when a mutually beneficial price is found.
    - 'minimum': Execute the minimum batch (starting from dA=1) that results in positive
      utility for both agents. Default for pedagogical clarity and backward compatibility.
    - 'maximum': Execute the maximum batch at the chosen price that still results in
      positive utility for both agents. More efficient but less pedagogical.
    """
    
    # --- Resource claiming system parameters ---
    enable_resource_claiming: bool = True  # Enable claim-based resource allocation
    enforce_single_harvester: bool = True  # Only one agent per resource cell per tick

    # --- Money system parameters (Phase 1+) ---
    
    exchange_regime: Literal["barter_only", "money_only", "mixed", "mixed_liquidity_gated"] = "barter_only"
    """
    Controls which types of exchanges are permitted in the TradeSystem.
    - 'barter_only': Only A<->B trades are allowed. Default for backward compatibility.
    - 'money_only': Only A<->M and B<->M trades are allowed.
    - 'mixed': All trade types (A<->B, A<->M, B<->M) are allowed.
    - 'mixed_liquidity_gated': Monetary trades are always allowed; barter is only
      allowed if the monetary market is considered "thin" (see liquidity_gate).
    """

    money_mode: Literal["quasilinear", "kkt_lambda"] = "quasilinear"
    """
    Determines how the marginal utility of money (lambda) is handled.
    - 'quasilinear': Lambda is a fixed constant provided by `lambda_money`. Total
      utility is U(A,B) + lambda * M.
    - 'kkt_lambda': Lambda is endogenously estimated by each agent based on
      observed market prices for goods in terms of money.
    """

    money_scale: int = 1
    """
    The scale factor for money, representing minor units. E.g., a scale of 100
    means M=100 is equivalent to 1 major unit of currency. All calculations are
    done in minor units. Must be >= 1.
    """

    lambda_money: float = 1.0
    """
    The fixed marginal utility of money (λ) used in 'quasilinear' mode. Must be positive.
    """

    money_utility_form: Literal["linear", "log"] = "linear"
    """
    Functional form for money utility component.
    - 'linear': U_money = λ·M (constant marginal utility)
    - 'log': U_money = λ·log(M + M_0) (diminishing marginal utility)
    """

    M_0: float = 0.0
    """
    Shift parameter for logarithmic money utility. Prevents log(0) singularity
    and calibrates the curvature of money's marginal utility. Must be >= 0.
    Ignored when money_utility_form='linear'.
    """

    lambda_update_rate: float = 0.2
    """
    The smoothing factor (alpha) for updating lambda in 'kkt_lambda' mode.
    λ_new = (1 - α) * λ_old + α * λ_hat. Must be in [0, 1].
    """
    
    lambda_bounds: dict[str, float] = field(default_factory=lambda: {"lambda_min": 1e-6, "lambda_max": 1e6})
    """
    The minimum and maximum allowed values for lambda in 'kkt_lambda' mode.
    """

    liquidity_gate: dict[str, int] = field(default_factory=lambda: {"min_quotes": 3})
    """
    Configuration for the 'mixed_liquidity_gated' exchange regime.
    - 'min_quotes': The minimum number of unique monetary quotes an agent must
      observe for the market to be considered "thick", thus disabling barter.
    """

    earn_money_enabled: bool = False
    """
    Placeholder for future features where agents can earn money through activities
    other than trade (e.g., labor, production). Currently unused.
    """
    
    # --- Telemetry parameters ---
    log_preferences: bool = False
    """
    If True, log all agent preference rankings to the preferences table in the
    telemetry database. This provides detailed insight into pairing decisions but
    increases database size. Default is False for standard simulations.
    """

    def validate(self) -> None:
        """Validate simulation parameters."""
        if self.spread < 0:
            raise ValueError(f"spread must be non-negative, got {self.spread}")
        if self.vision_radius < 0:
            raise ValueError(f"vision_radius must be non-negative, got {self.vision_radius}")
        if self.interaction_radius < 0:
            raise ValueError(f"interaction_radius must be non-negative, got {self.interaction_radius}")
        if self.move_budget_per_tick <= 0:
            raise ValueError(f"move_budget_per_tick must be positive, got {self.move_budget_per_tick}")
        if self.dA_max <= 0:
            raise ValueError(f"dA_max must be positive, got {self.dA_max}")
        if self.forage_rate <= 0:
            raise ValueError(f"forage_rate must be positive, got {self.forage_rate}")
        if self.epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {self.epsilon}")
        if not 0 < self.beta <= 1:
            raise ValueError(f"beta must be in (0, 1], got {self.beta}")
        if self.resource_growth_rate < 0:
            raise ValueError(f"resource_growth_rate must be non-negative, got {self.resource_growth_rate}")
        if self.resource_max_amount <= 0:
            raise ValueError(f"resource_max_amount must be positive, got {self.resource_max_amount}")
        if self.resource_regen_cooldown < 0:
            raise ValueError(f"resource_regen_cooldown must be non-negative, got {self.resource_regen_cooldown}")
        if self.trade_cooldown_ticks < 0:
            raise ValueError(f"trade_cooldown_ticks must be non-negative, got {self.trade_cooldown_ticks}")
        
        # Money system validation
        if self.money_scale < 1:
            raise ValueError(f"money_scale must be >= 1, got {self.money_scale}")
        if self.lambda_money <= 0:
            raise ValueError(f"lambda_money must be positive, got {self.lambda_money}")
        if self.M_0 < 0:
            raise ValueError(f"M_0 must be non-negative, got {self.M_0}")
        if self.money_utility_form not in ["linear", "log"]:
            raise ValueError(f"money_utility_form must be 'linear' or 'log', got {self.money_utility_form}")
        if not 0 <= self.lambda_update_rate <= 1:
            raise ValueError(f"lambda_update_rate must be in [0, 1], got {self.lambda_update_rate}")
        if "lambda_min" in self.lambda_bounds and "lambda_max" in self.lambda_bounds:
            if self.lambda_bounds["lambda_min"] >= self.lambda_bounds["lambda_max"]:
                raise ValueError("lambda_min must be < lambda_max")
            if self.lambda_bounds["lambda_min"] <= 0:
                raise ValueError("lambda_min must be positive")
        if "min_quotes" in self.liquidity_gate:
            if self.liquidity_gate["min_quotes"] < 0:
                raise ValueError("liquidity_gate.min_quotes must be non-negative")


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
    
    # Protocol configuration (optional - defaults to legacy protocols)
    search_protocol: Optional[str] = None  # e.g., "legacy", "random_walk"
    matching_protocol: Optional[str] = None  # e.g., "legacy_three_pass", "random"
    bargaining_protocol: Optional[str] = None  # e.g., "legacy_compensating_block", "split_difference"
    
    def validate(self) -> None:
        """Validate scenario parameters."""
        # Grid size
        if self.N <= 0:
            raise ValueError(f"Grid size N must be positive, got {self.N}")
        
        # Agent count
        if self.agents <= 0:
            raise ValueError(f"Agent count must be positive, got {self.agents}")
        
        # Params validation
        self.params.validate()
        
        # Resource seed validation
        if not 0 <= self.resource_seed.density <= 1:
            raise ValueError(f"resource density must be in [0, 1], got {self.resource_seed.density}")
        
        if self.resource_seed.density <= 0:
            # No resources, no need to check amount
            pass
        elif isinstance(self.resource_seed.amount, int):
            if self.resource_seed.amount <= 0:
                raise ValueError(f"resource amount must be positive, got {self.resource_seed.amount}")
        
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
            
            elif util.type == "quadratic":
                if "A_star" not in util.params or "B_star" not in util.params:
                    raise ValueError("Quadratic utility requires 'A_star' and 'B_star' parameters")
                if "sigma_A" not in util.params or "sigma_B" not in util.params:
                    raise ValueError("Quadratic utility requires 'sigma_A' and 'sigma_B' parameters")
                if util.params["A_star"] <= 0 or util.params["B_star"] <= 0:
                    raise ValueError("Quadratic bliss points must be positive")
                if util.params["sigma_A"] <= 0 or util.params["sigma_B"] <= 0:
                    raise ValueError("Quadratic curvature parameters must be positive")
                # gamma is optional, defaults to 0.0
                if "gamma" in util.params and util.params["gamma"] < 0:
                    raise ValueError("Quadratic cross-curvature gamma must be non-negative")
            
            elif util.type == "translog":
                required = ["alpha_0", "alpha_A", "alpha_B", "beta_AA", "beta_BB", "beta_AB"]
                for param in required:
                    if param not in util.params:
                        raise ValueError(f"Translog utility requires '{param}' parameter")
                if util.params["alpha_A"] <= 0 or util.params["alpha_B"] <= 0:
                    raise ValueError("Translog first-order coefficients (alpha_A, alpha_B) must be positive for monotonicity")
            
            elif util.type == "stone_geary":
                if "alpha_A" not in util.params or "alpha_B" not in util.params:
                    raise ValueError("Stone-Geary utility requires 'alpha_A' and 'alpha_B' parameters")
                if "gamma_A" not in util.params or "gamma_B" not in util.params:
                    raise ValueError("Stone-Geary utility requires 'gamma_A' and 'gamma_B' parameters")
                if util.params["alpha_A"] <= 0 or util.params["alpha_B"] <= 0:
                    raise ValueError("Stone-Geary preference weights must be positive")
                if util.params["gamma_A"] < 0 or util.params["gamma_B"] < 0:
                    raise ValueError("Stone-Geary subsistence levels must be non-negative")
                
                # Critical: Validate initial inventories > subsistence
                gamma_A = util.params["gamma_A"]
                gamma_B = util.params["gamma_B"]
                
                # Check A inventory
                inv_A = self.initial_inventories.get('A')
                if inv_A is not None:
                    if isinstance(inv_A, int):
                        if inv_A <= gamma_A:
                            raise ValueError(
                                f"Stone-Geary requires initial_inventories['A']={inv_A} > gamma_A={gamma_A}"
                            )
                    elif isinstance(inv_A, dict) and 'uniform_int' in inv_A:
                        min_A = inv_A['uniform_int'][0]
                        if min_A <= gamma_A:
                            raise ValueError(
                                f"Stone-Geary requires min(initial_inventories['A'])={min_A} > gamma_A={gamma_A}"
                            )
                
                # Check B inventory
                inv_B = self.initial_inventories.get('B')
                if inv_B is not None:
                    if isinstance(inv_B, int):
                        if inv_B <= gamma_B:
                            raise ValueError(
                                f"Stone-Geary requires initial_inventories['B']={inv_B} > gamma_B={gamma_B}"
                            )
                    elif isinstance(inv_B, dict) and 'uniform_int' in inv_B:
                        min_B = inv_B['uniform_int'][0]
                        if min_B <= gamma_B:
                            raise ValueError(
                                f"Stone-Geary requires min(initial_inventories['B'])={min_B} > gamma_B={gamma_B}"
                            )
        
        # Validate mode schedule if present
        if self.mode_schedule:
            self.mode_schedule.validate()

        # Money inventory validation
        if self.params.exchange_regime in ["money_only", "mixed", "mixed_liquidity_gated"]:
            if "M" not in self.initial_inventories:
                raise ValueError(
                    f"exchange_regime={self.params.exchange_regime} requires M in initial_inventories"
                )
        
        # Validate protocol names if specified (lazy import to ensure registry is populated)
        # Force protocol modules to import so decorators run and register entries
        import vmt_engine.protocols.search as _protocols_search  # noqa: F401
        import vmt_engine.protocols.matching as _protocols_matching  # noqa: F401
        import vmt_engine.protocols.bargaining as _protocols_bargaining  # noqa: F401

        from vmt_engine.protocols.registry import ProtocolRegistry
        registered = ProtocolRegistry.list_protocols()

        if self.search_protocol is not None and self.search_protocol not in registered.get('search', []):
            raise ValueError(
                f"Invalid search_protocol '{self.search_protocol}'. Available: {registered.get('search', [])}"
            )
        
        if self.matching_protocol is not None and self.matching_protocol not in registered.get('matching', []):
            raise ValueError(
                f"Invalid matching_protocol '{self.matching_protocol}'. Available: {registered.get('matching', [])}"
            )
        
        if self.bargaining_protocol is not None and self.bargaining_protocol not in registered.get('bargaining', []):
            raise ValueError(
                f"Invalid bargaining_protocol '{self.bargaining_protocol}'. Available: {registered.get('bargaining', [])}"
            )

