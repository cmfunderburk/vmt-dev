# Telemetry and Debugging

VMT uses SQLite database at `./logs/telemetry.db` for comprehensive simulation logging.

## Database Schema

### Core Tables

**`simulation_runs`** - Run metadata
```sql
CREATE TABLE simulation_runs (
    run_id INTEGER PRIMARY KEY,
    scenario_name TEXT,
    start_time TEXT,
    end_time TEXT,
    n_agents INTEGER,
    grid_width INTEGER,
    grid_height INTEGER,
    max_ticks INTEGER,
    config_json TEXT  -- Full scenario parameters
)
```

**`agent_snapshots`** - Per-tick agent state
```sql
CREATE TABLE agent_snapshots (
    run_id, tick, agent_id,
    pos_x, pos_y,
    inv_A, inv_B,
    utility REAL,
    target_pos_x, target_pos_y,
    paired_with_id INTEGER,
    ask_A_in_B, bid_A_in_B,  -- Quotes
    ...
)
```

**`trades`** - Successful trades
```sql
CREATE TABLE trades (
    run_id, tick,
    agent_i, agent_j,
    delta_A, delta_B,  -- Quantities exchanged
    price REAL,
    surplus_i REAL, surplus_j REAL,  -- Utility gains
    exchange_pair TEXT  -- "A<->B" for barter
)
```

**`pairings`** - Pairing events
```sql
CREATE TABLE pairings (
    run_id, tick,
    agent_i, agent_j,
    event TEXT,  -- "pair" | "unpair"
    reason TEXT,  -- "mutual_consent" | "greedy_fallback" | "trade_failed"
    surplus_i REAL, surplus_j REAL
)
```

**`preferences`** - Agent preference rankings
```sql
CREATE TABLE preferences (
    run_id, tick, agent_id,
    partner_id, rank,
    surplus REAL,
    discounted_surplus REAL,  -- surplus × β^distance
    distance INTEGER
)
```

## Logging Configuration

```python
from telemetry.config import LogConfig, LogLevel

# Standard logging (default)
log_config = LogConfig.standard()

# Debug logging (includes preferences, full details)
log_config = LogConfig.debug()

# Minimal logging (no per-tick snapshots)
log_config = LogConfig(
    level=LogLevel.INFO,
    use_database=True,
    log_agent_snapshots=False,
    log_preferences=False
)

sim = Simulation(scenario, seed=42, log_config=log_config)
```

## Viewing Telemetry

### GUI Log Viewer

```bash
python view_logs.py
```

Features:
- Timeline scrubbing (tick-by-tick navigation)
- Agent trajectory visualization
- Trade history filtering
- Preference list inspection
- Export to CSV

### SQL Queries

```python
import sqlite3

conn = sqlite3.connect('./logs/telemetry.db')
conn.row_factory = sqlite3.Row  # Access by column name

# Get all trades for a run
cursor = conn.execute("""
    SELECT tick, agent_i, agent_j, delta_A, delta_B, price, surplus_i, surplus_j
    FROM trades 
    WHERE run_id = ?
    ORDER BY tick
""", (run_id,))

for row in cursor:
    print(f"Tick {row['tick']}: Agent {row['agent_i']} ↔ {row['agent_j']}")
    print(f"  Exchanged: {row['delta_A']} A for {row['delta_B']} B")
    print(f"  Price: {row['price']:.3f}, Surplus: {row['surplus_i']:.2f} / {row['surplus_j']:.2f}")
```

## Common Queries

### Trade Analysis

```sql
-- Trade summary by agent
SELECT 
    agent_i as agent,
    COUNT(*) as trade_count,
    SUM(surplus_i) as total_surplus
FROM trades
WHERE run_id = ?
GROUP BY agent_i
ORDER BY total_surplus DESC;

-- Price convergence over time
SELECT tick, AVG(price) as avg_price, STDEV(price) as price_std
FROM trades
WHERE run_id = ?
GROUP BY tick
ORDER BY tick;
```

### Pairing Analysis

```sql
-- Pairing duration distribution
SELECT 
    agent_i, agent_j,
    MIN(tick) as pair_start,
    MAX(tick) as pair_end,
    MAX(tick) - MIN(tick) as duration
FROM pairings
WHERE run_id = ? AND event = 'pair'
GROUP BY agent_i, agent_j;

-- Pairing success rates
SELECT 
    reason,
    COUNT(*) as count
FROM pairings
WHERE run_id = ? AND event = 'pair'
GROUP BY reason;
```

### Spatial Patterns

```sql
-- Agent positions over time
SELECT tick, agent_id, pos_x, pos_y, paired_with_id
FROM agent_snapshots
WHERE run_id = ? AND agent_id = ?
ORDER BY tick;

-- Trade locations (heatmap data)
SELECT 
    a.pos_x, a.pos_y,
    COUNT(*) as trade_count
FROM trades t
JOIN agent_snapshots a ON 
    t.run_id = a.run_id AND 
    t.tick = a.tick AND 
    t.agent_i = a.agent_id
WHERE t.run_id = ?
GROUP BY a.pos_x, a.pos_y;
```

## Programmatic Access

```python
from telemetry import TelemetryManager, LogConfig

# Access telemetry during simulation
sim = Simulation(scenario, seed=42)
sim.run(max_ticks=100)

# Recent trades (for renderer)
recent_trades = sim.telemetry.recent_trades_for_renderer

# Full database access
db_path = sim.telemetry.db.db_path
conn = sqlite3.connect(db_path)

# Query specific run
run_id = sim.telemetry.run_id
cursor = conn.execute(
    "SELECT * FROM agent_snapshots WHERE run_id = ? AND tick = ?",
    (run_id, 50)
)
```

## Debug Logging

Enable detailed logging for debugging:

```python
# In simulation code
log_config = LogConfig.debug()
log_config.log_preferences = True  # Log full preference lists

sim = Simulation(scenario, seed=42, log_config=log_config)
sim.run(max_ticks=20)

# Check what was logged
conn = sqlite3.connect(sim.telemetry.db.db_path)

# Examine preferences for specific agent/tick
cursor = conn.execute("""
    SELECT partner_id, rank, surplus, discounted_surplus, distance
    FROM preferences
    WHERE run_id = ? AND tick = ? AND agent_id = ?
    ORDER BY rank
""", (sim.telemetry.run_id, 10, 1))

for row in cursor:
    print(f"Rank {row[1]}: Partner {row[0]}, Surplus {row[2]:.2f}")
```

## Performance Considerations

**Batch logging** (implemented by default):
- Agent snapshots buffered per phase
- Batch INSERT every N snapshots
- Trade, pairing, preference events buffered per tick

**Disable expensive logging** for large runs:
```python
log_config = LogConfig(
    level=LogLevel.INFO,
    log_agent_snapshots=False,  # Skip per-tick snapshots
    log_preferences=False        # Skip preference lists
)
```

**Database optimization**:
- WAL mode enabled (better concurrent access)
- Indices on `(run_id, tick)` for fast queries
- Foreign keys enforced for referential integrity

## Debugging Scenarios

### Problem: Trade not happening
```sql
-- Check if agents are paired
SELECT tick, agent_id, paired_with_id, target_pos_x, target_pos_y
FROM agent_snapshots
WHERE run_id = ? AND agent_id IN (?, ?)
ORDER BY tick;

-- Check if in interaction range
SELECT tick, agent_id, pos_x, pos_y
FROM agent_snapshots
WHERE run_id = ? AND agent_id IN (?, ?)
ORDER BY tick;

-- Check trade cooldowns (look at pairing events)
SELECT tick, event, reason
FROM pairings
WHERE run_id = ? AND agent_i IN (?, ?) OR agent_j IN (?, ?)
ORDER BY tick;
```

### Problem: Non-determinism
```sql
-- Compare two runs tick-by-tick
SELECT a1.tick, a1.pos_x, a1.pos_y, a2.pos_x, a2.pos_y
FROM agent_snapshots a1
JOIN agent_snapshots a2 ON a1.tick = a2.tick AND a1.agent_id = a2.agent_id
WHERE a1.run_id = ? AND a2.run_id = ?
  AND (a1.pos_x != a2.pos_x OR a1.pos_y != a2.pos_y)
ORDER BY a1.tick
LIMIT 1;  -- First tick where divergence occurs
```

### Problem: Price not converging
```sql
-- Track price evolution
SELECT 
    tick,
    COUNT(*) as trade_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    STDEV(price) as price_std
FROM trades
WHERE run_id = ?
GROUP BY tick
ORDER BY tick;
```

## Telemetry Schema Updates

When adding new telemetry:

1. Update schema in `src/telemetry/database.py`
2. Add logging method in `src/telemetry/db_loggers.py`
3. Call from appropriate system in `src/vmt_engine/systems/`
4. Update this documentation

Example:
```python
# database.py
cursor.execute("""
    CREATE TABLE IF NOT EXISTS my_new_table (
        id INTEGER PRIMARY KEY,
        run_id INTEGER NOT NULL,
        tick INTEGER NOT NULL,
        my_data TEXT,
        FOREIGN KEY (run_id) REFERENCES simulation_runs(run_id)
    )
""")

# db_loggers.py
def log_my_event(self, tick: int, data: str):
    if not self.config.use_database:
        return
    self.db.execute(
        "INSERT INTO my_new_table (run_id, tick, my_data) VALUES (?, ?, ?)",
        (self.run_id, tick, data)
    )
    self.db.commit()
```

