"""
Logging configuration for telemetry system.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class LogLevel(IntEnum):
    """Logging verbosity levels."""
    STANDARD = 1   # Decisions + trades + periodic snapshots (default)
    DEBUG = 2      # Everything including failed trade attempts
    
    @classmethod
    def from_string(cls, level: str) -> 'LogLevel':
        """Convert string to LogLevel."""
        level_map = {
            'standard': cls.STANDARD,
            'debug': cls.DEBUG,
        }
        return level_map.get(level.lower(), cls.STANDARD)


@dataclass
class LogConfig:
    """Configuration for telemetry logging."""
    
    # Global log level
    level: LogLevel = LogLevel.STANDARD
    
    # Snapshot frequencies (0 = disabled)
    agent_snapshot_frequency: int = 1    # Every N ticks
    resource_snapshot_frequency: int = 10  # Every N ticks
    
    # Individual logger enables (can override level)
    log_trades: bool = True
    log_trade_attempts: bool = False  # Only in DEBUG mode by default
    log_decisions: bool = True
    log_agent_snapshots: bool = True
    log_resource_snapshots: bool = True
    
    # Database settings
    use_database: bool = True
    db_path: Optional[str] = None  # If None, use default
    
    # Legacy CSV support
    export_csv: bool = False
    csv_dir: Optional[str] = None
    
    # Batch settings for performance
    batch_size: int = 100  # Commit to DB every N records
    
    def __post_init__(self):
        """Adjust settings based on log level."""
        if self.level == LogLevel.DEBUG:
            self.log_trade_attempts = True
        else:
            self.log_trade_attempts = False
    
    @classmethod
    def standard(cls) -> 'LogConfig':
        """Create a standard-level config."""
        return cls(level=LogLevel.STANDARD)
    
    @classmethod
    def debug(cls) -> 'LogConfig':
        """Create a debug-level config."""
        return cls(level=LogLevel.DEBUG)
    
    @classmethod
    def minimal(cls) -> 'LogConfig':
        """Create a minimal config for testing (no snapshots, only trades)."""
        return cls(
            level=LogLevel.STANDARD,
            agent_snapshot_frequency=0,
            resource_snapshot_frequency=0,
            log_decisions=False,
            log_trade_attempts=False,
            log_agent_snapshots=False,
            log_resource_snapshots=False
        )

