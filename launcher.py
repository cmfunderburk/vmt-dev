#!/usr/bin/env python
"""
Entry point for VMT Simulation GUI Launcher.

Usage:
    python launcher.py
"""

import sys
import os

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Clear any invalid style overrides to ensure cross-platform compatibility
# (kvantum and other platform-specific styles may not be available on all systems)
if 'QT_STYLE_OVERRIDE' in os.environ:
    del os.environ['QT_STYLE_OVERRIDE']

from PyQt6.QtWidgets import QApplication
from vmt_launcher.launcher import LauncherWindow


def main():
    """Main entry point for the GUI launcher."""
    app = QApplication(sys.argv)
    # Ensure cross-platform compatible style (Fusion works on all platforms)
    app.setStyle("Fusion")
    # Set application to quit when last window closes (important for Linux)
    app.setQuitOnLastWindowClosed(True)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

