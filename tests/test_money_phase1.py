"""
Unit tests for Phase 1 money system infrastructure.
"""

import pytest
from scenarios.schema import ScenarioParams
from vmt_engine.core.state import Inventory
from vmt_engine.core.agent import Agent


def test_money_params_defaults():
    """Verify default money params don't break existing scenarios."""
    params = ScenarioParams()
    assert params.exchange_regime == "barter_only"
    assert params.money_scale == 1
    params.validate()  # Should not raise


def test_money_params_validation():
    """Verify money param validation."""
    # Invalid money_scale
    with pytest.raises(ValueError, match="money_scale must be >= 1"):
        p = ScenarioParams(money_scale=0)
        p.validate()

    # Invalid lambda bounds
    with pytest.raises(ValueError, match="lambda_min must be < lambda_max"):
        p = ScenarioParams(lambda_bounds={"lambda_min": 1.0, "lambda_max": 0.5})
        p.validate()
        
    # Invalid lambda update rate
    with pytest.raises(ValueError, match="lambda_update_rate must be in"):
        p = ScenarioParams(lambda_update_rate=1.1)
        p.validate()


def test_inventory_with_money():
    """Verify Inventory accepts M field and validates it."""
    inv = Inventory(A=10, B=20, M=100)
    assert inv.M == 100

    with pytest.raises(ValueError, match="Inventory cannot be negative"):
        Inventory(A=10, B=20, M=-5)


def test_agent_lambda_initialization():
    """Verify agents initialize with default money state."""
    agent = Agent(
        id=0, pos=(0, 0),
        inventory=Inventory(A=5, B=5, M=50),
        utility=None, vision_radius=5, move_budget_per_tick=1
    )
    assert agent.lambda_money == 1.0
    assert not agent.lambda_changed
    assert agent.inventory.M == 50
