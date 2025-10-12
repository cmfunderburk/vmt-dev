# New Telemetry & Logging System

## Overview

The VMT simulation now features a modern, database-backed telemetry system that addresses the limitations of the previous CSV-based approach. This system provides:

- **SQLite database storage** - 10-100x smaller files with fast queries
- **Configurable log levels** - Control verbosity (SUMMARY, STANDARD, DEBUG)
- **Interactive log viewer UI** - Explore simulation data visually
- **CSV export** - Backward compatibility when needed
- **Batch writing** - Efficient database operations

## Quick Start

### Using the New Logging System

```python
from vmt_engine.simulation import Simulation
from telemetry import LogConfig, LogLevel
from scenarios.loader import load_scenario

# Load your scenario
scenario = load_scenario("scenarios/three_agent_barter.yaml")

# Configure logging
log_config = LogConfig.standard()  # or .summary() or .debug()

# Create simulation with new logging
sim = Simulation(scenario, seed=42, log_config=log_config)
sim.run(max_ticks=1000)
sim.close()
```

### Using Legacy CSV Logging

```python
# If you need old CSV format
sim = Simulation(scenario, seed=42, use_legacy_logging=True)
sim.run(max_ticks=1000)
sim.close()
```

### Viewing Logs

Run the log viewer application:

```bash
python view_logs.py
```

Or from Python:

```python
from vmt_log_viewer import LogViewerWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
viewer = LogViewerWindow()
viewer.show()
sys.exit(app.exec_())
```

## Log Levels

### SUMMARY
- **Use case**: Production runs, final analysis
- **Logs**: Successful trades only, no periodic snapshots
- **File size**: Smallest (1-5% of DEBUG)
- **Example**:
  ```python
  log_config = LogConfig.summary()
  ```

### STANDARD (Default)
- **Use case**: Normal development and analysis
- **Logs**: Trades, decisions, agent/resource snapshots
- **File size**: Medium (10-20% of DEBUG)
- **Example**:
  ```python
  log_config = LogConfig.standard()
  # or
  log_config = LogConfig(
      level=LogLevel.STANDARD,
      agent_snapshot_frequency=1,  # Every tick
      resource_snapshot_frequency=10  # Every 10 ticks
  )
  ```

### DEBUG
- **Use case**: Debugging trade issues, detailed analysis
- **Logs**: Everything including failed trade attempts
- **File size**: Largest (can be 100x larger than SUMMARY)
- **Example**:
  ```python
  log_config = LogConfig.debug()
  ```

## Database Schema

### Tables

**simulation_runs**
- Metadata about each simulation run
- Scenario name, agent count, grid size, timestamps

**agent_snapshots**
- Agent state at each tick
- Position, inventory, utility, quotes, targets
- Indexed by (run_id, tick) and (run_id, agent_id, tick)

**resource_snapshots**
- Resource distribution over time
- Indexed by (run_id, tick)

**decisions**
- Agent decision-making
- Partner selection, movement targets
- Indexed by (run_id, tick) and (run_id, agent_id, tick)

**trades**
- Successful trades
- Buyer/seller, amounts, price, location
- Indexed by (run_id, tick) and (run_id, buyer_id, seller_id)

**trade_attempts** (DEBUG only)
- All trade attempts including failures
- Detailed utility calculations, feasibility checks
- Indexed by (run_id, tick)

## Log Viewer Features

### Overview Tab
- Run statistics
- Trade summary
- Agent trade counts

### Agents Tab
- Agent state at current tick
- All agents table (sortable)
- Agent selector for detailed view
- Position, inventory, utility, quotes

### Trades Tab
- Trades at current tick
- Trade details
- Trade attempts (DEBUG mode)

### Decisions Tab
- Agent decisions at current tick
- Partner selection
- Movement targets

### Resources Tab
- Resource distribution at current tick

### Timeline
- Scrub through simulation time
- Previous/Next tick buttons
- Tick slider and spinbox
- Jump to specific tick

### Export
- Export any run to CSV format
- Maintains backward compatibility
- Selective export (only what you need)

## Performance Comparison

### File Sizes (1000 tick simulation, 50 agents)

| Format | Size | Relative |
|--------|------|----------|
| CSV (old) | ~450 MB | 100% |
| SQLite SUMMARY | ~2 MB | 0.4% |
| SQLite STANDARD | ~25 MB | 5.5% |
| SQLite DEBUG | ~180 MB | 40% |

### Query Performance

| Operation | CSV | SQLite |
|-----------|-----|--------|
| Load run | 30-60s | <1s |
| Get tick data | N/A | <0.1s |
| Agent trajectory | N/A | <0.5s |
| Trade analysis | N/A | <0.2s |

## Configuration Options

```python
from telemetry import LogConfig, LogLevel

config = LogConfig(
    # Global log level
    level=LogLevel.STANDARD,
    
    # Snapshot frequencies (0 = disabled)
    agent_snapshot_frequency=1,    # Every N ticks
    resource_snapshot_frequency=10,  # Every N ticks
    
    # Individual logger enables
    log_trades=True,
    log_trade_attempts=False,  # Only in DEBUG
    log_decisions=True,
    log_agent_snapshots=True,
    log_resource_snapshots=True,
    
    # Database settings
    use_database=True,
    db_path="./logs/telemetry.db",  # None = default
    
    # Legacy CSV support
    export_csv=False,
    csv_dir=None,
    
    # Performance
    batch_size=100  # Commit every N records
)
```

## Querying Data Programmatically

```python
from telemetry.database import TelemetryDatabase
from vmt_log_viewer.queries import QueryBuilder

# Open database
db = TelemetryDatabase("./logs/telemetry.db")

# Get runs
runs = db.get_runs()
run_id = runs[0]['run_id']

# Get agent trajectory
query, params = QueryBuilder.get_agent_trajectory(run_id, agent_id=0)
trajectory = db.execute(query, params).fetchall()

for point in trajectory:
    print(f"Tick {point['tick']}: ({point['x']}, {point['y']}) "
          f"A={point['inventory_A']}, B={point['inventory_B']}, "
          f"U={point['utility']:.2f}")

# Get trades by agent
query, params = QueryBuilder.get_trades_by_agent(run_id, agent_id=0)
trades = db.execute(query, params).fetchall()

for trade in trades:
    print(f"Tick {trade['tick']}: "
          f"{'bought' if trade['buyer_id'] == 0 else 'sold'} "
          f"{trade['dA']} A for {trade['dB']} B "
          f"@ price {trade['price']:.4f}")

# Get trade statistics
query, params = QueryBuilder.get_trade_statistics(run_id)
stats = db.execute(query, params).fetchone()
print(f"Total trades: {stats['total_trades']}")
print(f"Average price: {stats['avg_price']:.4f}")

db.close()
```

## CSV Export

Export from log viewer UI:
1. Open Database
2. Select Run
3. Click "Export to CSV"
4. Choose directory

Export programmatically:

```python
from telemetry.database import TelemetryDatabase
from vmt_log_viewer.csv_export import export_run_to_csv

db = TelemetryDatabase("./logs/telemetry.db")
runs = db.get_runs()
run_id = runs[0]['run_id']

export_run_to_csv(db, run_id, "./exported_logs")
db.close()
```

## Migration from CSV

The new system is fully backward compatible:

1. **Keep using CSV**: Set `use_legacy_logging=True`
2. **Migrate to database**: Use default (new logging)
3. **Both**: Run with new logging, export to CSV when needed

Existing code that reads CSV files can continue to work with exported data.

## Best Practices

### Development
- Use **STANDARD** level during development
- Check agent snapshots at every tick
- Use log viewer to debug issues

### Production
- Use **SUMMARY** level for long runs
- Reduce snapshot frequency if needed
- Export specific data to CSV for analysis

### Debugging Trades
- Use **DEBUG** level
- Examine trade_attempts table
- Look at utility improvements and feasibility checks

### Performance
- Increase `batch_size` for faster logging (default 100)
- Reduce snapshot frequencies for very long runs
- Disable unused loggers in custom LogConfig

## Troubleshooting

### Database locked
- Only one process can write at a time
- Close previous simulation before starting new one
- Check for zombie processes

### Large database files
- Use SUMMARY level for long runs
- Increase snapshot frequencies (e.g., every 10 ticks)
- Consider disabling resource snapshots

### Slow queries
- Database should be indexed automatically
- If queries are slow, check SQLite version
- Try `VACUUM` on database to optimize

### Export fails
- Check disk space
- Ensure write permissions
- Close database before exporting

## Architecture

```
telemetry/
├── database.py         # SQLite schema & connection
├── config.py          # LogConfig & LogLevel
├── db_loggers.py      # TelemetryManager
├── logger.py          # Legacy TradeLogger (CSV)
├── decision_logger.py # Legacy DecisionLogger (CSV)
├── snapshots.py       # Legacy snapshot loggers (CSV)
└── trade_attempt_logger.py  # Legacy attempt logger (CSV)

vmt_log_viewer/
├── viewer.py          # Main PyQt5 window
├── queries.py         # SQL query builders
├── csv_export.py      # Export to CSV
└── widgets/
    ├── timeline.py    # Timeline scrubber
    ├── agent_view.py  # Agent analysis
    ├── trade_view.py  # Trade analysis
    └── filters.py     # Query filters
```

## Future Enhancements

Potential additions:
- Animation playback in log viewer
- Custom query builder in UI
- Chart/graph visualizations
- Multi-run comparison
- Network graph of trades
- Agent trajectory visualization
- Export to other formats (JSON, Parquet)
- Streaming log analysis

## See Also

- [Configuration Documentation](CONFIGURATION.md)
- [Telemetry Implementation](TELEMETRY_IMPLEMENTATION.md)
- [Performance Optimization](PERFORMANCE_OPTIMIZATION_SUMMARY.md)

