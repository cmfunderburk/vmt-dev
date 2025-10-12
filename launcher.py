#!/usr/bin/env python
"""
Entry point for VMT Simulation GUI Launcher.

Usage:
    python launcher.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from vmt_launcher.launcher import LauncherWindow


def main():
    """Main entry point for the GUI launcher."""
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

