import pytest
from scenarios.schema import ModeSchedule


def test_mode_schedule_validation():
    """Test that invalid schedules raise appropriate errors."""
    with pytest.raises(ValueError):
        ModeSchedule(type="global_cycle", forage_ticks=-1, trade_ticks=5).validate()
    
    with pytest.raises(ValueError):
        ModeSchedule(type="global_cycle", forage_ticks=5, trade_ticks=0).validate()
    
    with pytest.raises(NotImplementedError):
        ModeSchedule(type="agent_specific", forage_ticks=5, trade_ticks=5).validate()


def test_mode_calculation_forage_start():
    """Test correct mode determination at various ticks with forage start."""
    schedule = ModeSchedule(type="global_cycle", forage_ticks=10, trade_ticks=5, start_mode="forage")
    schedule.validate()
    
    assert schedule.get_mode_at_tick(0) == "forage"
    assert schedule.get_mode_at_tick(9) == "forage"
    assert schedule.get_mode_at_tick(10) == "trade"
    assert schedule.get_mode_at_tick(14) == "trade"
    assert schedule.get_mode_at_tick(15) == "forage"  # New cycle
    assert schedule.get_mode_at_tick(30) == "forage"  # Multiple cycles


def test_mode_calculation_trade_start():
    """Test correct mode determination with trade start."""
    schedule = ModeSchedule(type="global_cycle", forage_ticks=10, trade_ticks=5, start_mode="trade")
    schedule.validate()
    
    assert schedule.get_mode_at_tick(0) == "trade"
    assert schedule.get_mode_at_tick(4) == "trade"
    assert schedule.get_mode_at_tick(5) == "forage"
    assert schedule.get_mode_at_tick(14) == "forage"
    assert schedule.get_mode_at_tick(15) == "trade"  # New cycle

