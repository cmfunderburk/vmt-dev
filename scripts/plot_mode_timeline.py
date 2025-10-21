#!/usr/bin/env python3
"""
Visualize mode transitions from VMT telemetry database.

Requires matplotlib for plotting.

Usage:
    python scripts/plot_mode_timeline.py <db_path> <run_id> [--output <filename>]

Example:
    python scripts/plot_mode_timeline.py runs.db 1
    python scripts/plot_mode_timeline.py runs.db 1 --output mode_timeline.png
"""

import sys
import sqlite3
from pathlib import Path


def plot_mode_timeline(db_path: str, run_id: int, output_file: str = None):
    """
    Plot mode timeline from telemetry data.
    
    Args:
        db_path: Path to SQLite telemetry database
        run_id: Run ID to analyze
        output_file: Optional output filename (if None, displays interactively)
    """
    # Import matplotlib here so script can still run without it for --help
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("Error: matplotlib is required for plotting")
        print("Install with: pip install matplotlib")
        sys.exit(1)
    
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    
    # Get mode data
    cursor = conn.execute("""
        SELECT tick, current_mode, exchange_regime 
        FROM tick_states 
        WHERE run_id = ?
        ORDER BY tick
    """, (run_id,))
    
    data = list(cursor)
    conn.close()
    
    if not data:
        print(f"No tick_states data found for run_id {run_id}")
        return
    
    ticks = [row[0] for row in data]
    modes = [row[1] for row in data]
    regime = data[0][2] if len(data) > 0 else "unknown"
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 4))
    
    # Color code modes
    mode_colors = {
        'forage': '#2ecc71',  # Green
        'trade': '#3498db',    # Blue
        'both': '#9b59b6'      # Purple
    }
    
    # Plot mode timeline as colored vertical spans
    current_mode = modes[0]
    start_tick = ticks[0]
    
    for i, (tick, mode) in enumerate(zip(ticks, modes)):
        if mode != current_mode or i == len(ticks) - 1:
            # Draw span for previous mode
            end_tick = tick if i < len(ticks) - 1 else tick + 1
            color = mode_colors.get(current_mode, '#95a5a6')
            ax.axvspan(start_tick, end_tick, alpha=0.3, color=color, 
                      label=current_mode if current_mode not in [m for _, m, _ in data[:i]] else "")
            
            # Start new span
            current_mode = mode
            start_tick = tick
    
    # Draw final span
    if len(ticks) > 0:
        color = mode_colors.get(current_mode, '#95a5a6')
        ax.axvspan(start_tick, ticks[-1] + 1, alpha=0.3, color=color)
    
    # Formatting
    ax.set_xlabel('Tick', fontsize=12)
    ax.set_ylabel('Mode', fontsize=12)
    ax.set_title(f'Mode Timeline (Run {run_id}, Regime: {regime})', fontsize=14, fontweight='bold')
    ax.set_ylim(-0.5, 0.5)
    ax.set_yticks([])
    ax.grid(True, axis='x', alpha=0.3)
    
    # Legend
    patches = [
        mpatches.Patch(color=mode_colors['forage'], alpha=0.3, label='Forage Mode'),
        mpatches.Patch(color=mode_colors['trade'], alpha=0.3, label='Trade Mode'),
        mpatches.Patch(color=mode_colors['both'], alpha=0.3, label='Both Mode')
    ]
    ax.legend(handles=patches, loc='upper right')
    
    # Add mode labels
    y_pos = 0
    for tick, mode in zip(ticks[::max(1, len(ticks)//20)], modes[::max(1, len(ticks)//20)]):
        ax.text(tick, y_pos, mode.capitalize(), 
               ha='center', va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    else:
        plt.show()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Visualize mode transitions from VMT telemetry database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s runs.db 1
  %(prog)s runs.db 1 --output mode_timeline.png
        """
    )
    
    parser.add_argument('db_path', help='Path to SQLite telemetry database')
    parser.add_argument('run_id', type=int, help='Run ID to analyze')
    parser.add_argument('--output', '-o', help='Output filename (if not provided, displays interactively)')
    
    args = parser.parse_args()
    
    try:
        plot_mode_timeline(args.db_path, args.run_id, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

