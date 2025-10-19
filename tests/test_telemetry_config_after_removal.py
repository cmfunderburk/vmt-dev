"""
Unit tests for telemetry configuration after summary logging removal.

Verifies that:
- SUMMARY level no longer exists
- summary() factory method no longer exists
- STANDARD and DEBUG levels work correctly
- from_string() handles missing levels gracefully
- minimal() factory uses STANDARD base level
"""

import pytest
from telemetry.config import LogConfig, LogLevel


def test_loglevel_enum_values():
    """Verify STANDARD and DEBUG levels exist with correct values."""
    assert LogLevel.STANDARD == 1
    assert LogLevel.DEBUG == 2


def test_loglevel_summary_removed():
    """Verify SUMMARY level no longer exists."""
    assert not hasattr(LogLevel, 'SUMMARY')


def test_from_string_standard():
    """Verify from_string() correctly converts 'standard'."""
    assert LogLevel.from_string("standard") == LogLevel.STANDARD
    assert LogLevel.from_string("STANDARD") == LogLevel.STANDARD
    assert LogLevel.from_string("Standard") == LogLevel.STANDARD


def test_from_string_debug():
    """Verify from_string() correctly converts 'debug'."""
    assert LogLevel.from_string("debug") == LogLevel.DEBUG
    assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
    assert LogLevel.from_string("Debug") == LogLevel.DEBUG


def test_from_string_summary_returns_default():
    """Verify from_string('summary') returns default (STANDARD)."""
    # After removal, 'summary' should default to STANDARD
    assert LogLevel.from_string("summary") == LogLevel.STANDARD


def test_from_string_unknown_returns_default():
    """Verify from_string() returns STANDARD for unknown values."""
    assert LogLevel.from_string("unknown") == LogLevel.STANDARD
    assert LogLevel.from_string("invalid") == LogLevel.STANDARD
    assert LogLevel.from_string("") == LogLevel.STANDARD


def test_logconfig_summary_method_removed():
    """Verify summary() factory method no longer exists."""
    assert not hasattr(LogConfig, 'summary')


def test_logconfig_standard_factory():
    """Verify standard() factory creates correct configuration."""
    cfg = LogConfig.standard()
    assert cfg.level == LogLevel.STANDARD
    assert cfg.log_trades == True
    assert cfg.log_decisions == True
    assert cfg.log_agent_snapshots == True
    assert cfg.log_resource_snapshots == True
    assert cfg.log_trade_attempts == False  # Only enabled in DEBUG


def test_logconfig_debug_factory():
    """Verify debug() factory creates correct configuration."""
    cfg = LogConfig.debug()
    assert cfg.level == LogLevel.DEBUG
    assert cfg.log_trades == True
    assert cfg.log_decisions == True
    assert cfg.log_agent_snapshots == True
    assert cfg.log_resource_snapshots == True
    assert cfg.log_trade_attempts == True  # Enabled in DEBUG


def test_logconfig_minimal_factory():
    """Verify minimal() factory uses STANDARD base level."""
    cfg = LogConfig.minimal()
    assert cfg.level == LogLevel.STANDARD  # Changed from SUMMARY
    assert cfg.agent_snapshot_frequency == 0
    assert cfg.resource_snapshot_frequency == 0
    assert cfg.log_decisions == False
    assert cfg.log_trade_attempts == False
    assert cfg.log_agent_snapshots == False
    assert cfg.log_resource_snapshots == False


def test_logconfig_default_level():
    """Verify default LogConfig uses STANDARD level."""
    cfg = LogConfig()
    assert cfg.level == LogLevel.STANDARD


def test_logconfig_post_init_standard():
    """Verify __post_init__ correctly configures STANDARD level."""
    cfg = LogConfig(level=LogLevel.STANDARD)
    assert cfg.log_trade_attempts == False


def test_logconfig_post_init_debug():
    """Verify __post_init__ correctly configures DEBUG level."""
    cfg = LogConfig(level=LogLevel.DEBUG)
    assert cfg.log_trade_attempts == True


def test_logconfig_use_database_false():
    """Verify use_database=False disables database logging."""
    cfg = LogConfig(use_database=False)
    assert cfg.use_database == False
    assert cfg.level == LogLevel.STANDARD  # Still has a level


def test_logconfig_custom_frequencies():
    """Verify custom snapshot frequencies can be set."""
    cfg = LogConfig(
        agent_snapshot_frequency=5,
        resource_snapshot_frequency=20
    )
    assert cfg.agent_snapshot_frequency == 5
    assert cfg.resource_snapshot_frequency == 20


def test_logconfig_batch_size_default():
    """Verify default batch size is 100."""
    cfg = LogConfig()
    assert cfg.batch_size == 100


def test_logconfig_immutable_after_init():
    """Verify that level-based settings are applied at init."""
    # Create with DEBUG, then manually change level
    # The __post_init__ settings should not change
    cfg = LogConfig(level=LogLevel.DEBUG)
    assert cfg.log_trade_attempts == True
    
    # Manually changing level doesn't re-run __post_init__
    cfg.level = LogLevel.STANDARD
    assert cfg.log_trade_attempts == True  # Still True from DEBUG init

