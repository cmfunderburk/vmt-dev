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

from PyQt6.QtWidgets import QApplication
from vmt_launcher.launcher import LauncherWindow


def main():
    """Main entry point for the GUI launcher."""
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

