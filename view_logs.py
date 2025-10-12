#!/usr/bin/env python3
"""
Launch the log viewer application.
"""

import sys
from vmt_log_viewer import LogViewerWindow
from PyQt5.QtWidgets import QApplication


def main():
    """Run the log viewer application."""
    app = QApplication(sys.argv)
    viewer = LogViewerWindow()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

