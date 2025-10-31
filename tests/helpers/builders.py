from typing import Union
from scenarios.schema import (
    ScenarioConfig,
    ScenarioParams,
    UtilitiesMix,
    UtilityConfig,
    ResourceSeed,
)
from vmt_engine.simulation import Simulation
from scenarios.protocol_factory import (
    get_search_protocol,
    get_matching_protocol,
    get_bargaining_protocol,
)


def build_scenario(
    N: int = 8,
    agents: int = 10,
    regime: str = "barter_only",  # Kept for backward compatibility, but ignored
    name: str = "test_scenario",
    resource_density: float = 0.0,
) -> ScenarioConfig:
    """Construct a minimal valid ScenarioConfig with complementary endowments.

    - Alternates A-rich and B-rich to encourage trade
    - Uses CES utility mix by default for simplicity
    - Sets reasonable defaults that match engine expectations
    
    Note: regime parameter is deprecated and ignored (barter-only economy).
    """
    inventories_A = [8 if i % 2 == 0 else 2 for i in range(agents)]
    inventories_B = [2 if i % 2 == 0 else 8 for i in range(agents)]

    params = ScenarioParams(
        vision_radius=N,
        interaction_radius=1,
        move_budget_per_tick=3,
        forage_rate=1,
        epsilon=1e-9,
        beta=0.95,
        resource_growth_rate=1,
        resource_max_amount=3,
        resource_regen_cooldown=8,
        trade_cooldown_ticks=5,
    )

    return ScenarioConfig(
        schema_version=1,
        name=name,
        N=N,
        agents=agents,
        initial_inventories={
            "A": inventories_A,
            "B": inventories_B,
        },
        utilities=UtilitiesMix(
            mix=[
                UtilityConfig(type="ces", weight=0.6, params={"rho": -0.5, "wA": 1.0, "wB": 1.0}),
                UtilityConfig(type="linear", weight=0.4, params={"vA": 1.0, "vB": 1.2}),
            ]
        ),
        params=params,
        resource_seed=ResourceSeed(density=resource_density, amount=1),
        # Set protocol fields explicitly to avoid test failures
        search_protocol="legacy_distance_discounted",
        matching_protocol="legacy_three_pass", 
        bargaining_protocol="legacy_compensating_block",
    )


def make_sim(
    scenario: ScenarioConfig,
    seed: int = 42,
    search: Union[str, dict, None] = None,
    matching: Union[str, dict, None] = None,
    bargaining: Union[str, dict, None] = None,
) -> Simulation:
    """Create a Simulation with optional protocol overrides by name or config dict.

    If a protocol name/config is provided, instantiate via the protocol factory and
    pass the instance to Simulation to override defaults.
    
    Args:
        scenario: Scenario configuration
        seed: Random seed
        search: Protocol name (str) or config dict (e.g., {"name": "myopic", "params": {}})
        matching: Protocol name (str) or config dict
        bargaining: Protocol name (str) or config dict (e.g., {"name": "take_it_or_leave_it", "params": {"proposer_power": 0.9}})
    """
    search_obj = get_search_protocol(search) if search else None
    matching_obj = get_matching_protocol(matching) if matching else None
    bargaining_obj = get_bargaining_protocol(bargaining) if bargaining else None

    return Simulation(
        scenario,
        seed=seed,
        search_protocol=search_obj,
        matching_protocol=matching_obj,
        bargaining_protocol=bargaining_obj,
    )


