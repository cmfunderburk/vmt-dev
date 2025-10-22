#!/usr/bin/env python3
"""
Launch the log viewer application.
"""

import sys
import os

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from vmt_log_viewer import LogViewerWindow
from PyQt6.QtWidgets import QApplication


def main():
    """Run the log viewer application."""
    app = QApplication(sys.argv)
    viewer = LogViewerWindow()
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

