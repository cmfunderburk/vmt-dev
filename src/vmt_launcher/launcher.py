"""
Main launcher window for VMT simulation.
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLineEdit, QLabel,
    QMessageBox, QApplication, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QKeySequence, QShortcut, QCloseEvent
from .scenario_builder import ScenarioBuilderDialog

# Assumes the script is run from the project root
SCENARIOS_DIR = "scenarios"

def find_scenario_files():
    """
    Find all YAML scenario files in the scenarios directory (recursive).
    
    Returns:
        List of (display_name, full_path) tuples
        display_name includes folder path relative to scenarios/
    """
    scenarios_path = Path(SCENARIOS_DIR)
    
    if not scenarios_path.exists():
        return []
    
    yaml_files = []
    
    # Recursively find all .yaml files
    for file in scenarios_path.rglob("*.yaml"):
        if file.is_file():
            # Get relative path from scenarios directory
            relative_path = file.relative_to(scenarios_path)
            display_name = str(relative_path)
            yaml_files.append((display_name, str(file)))
    
    # Sort by display name (will naturally group by folder)
    yaml_files.sort(key=lambda x: x[0])
    
    return yaml_files


class LauncherWindow(QMainWindow):
    """Main launcher window for VMT simulations."""
    
    def __init__(self):
        super().__init__()
        self.selected_scenario = None
        self.init_ui()
        self.refresh_scenarios()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("VMT Simulation Launcher")
        self.setGeometry(100, 100, 500, 600)
        
        # Set window attribute to ensure proper closing on Linux
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Set up keyboard shortcuts for quitting
        # Ctrl+D to quit
        quit_shortcut_d = QShortcut(QKeySequence("Ctrl+D"), self)
        quit_shortcut_d.activated.connect(self.quit_application)
        
        # Ctrl+Q to quit (standard)
        quit_shortcut_q = QShortcut(QKeySequence.StandardKey.Quit, self)
        quit_shortcut_q.activated.connect(self.quit_application)
        
        # Ctrl+W to close window
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.quit_application)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create Custom Scenario button at top
        self.create_scenario_btn = QPushButton("Create Custom Scenario")
        self.create_scenario_btn.clicked.connect(self.open_scenario_builder)
        layout.addWidget(self.create_scenario_btn)
        
        # Separator
        layout.addSpacing(10)
        
        # Scenario selection label
        scenario_label = QLabel("Select Scenario:")
        scenario_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(scenario_label)
        
        # Scenario list
        self.scenario_list = QListWidget()
        self.scenario_list.itemClicked.connect(self.on_scenario_selected)
        layout.addWidget(self.scenario_list)
        
        # Seed input
        seed_layout = QHBoxLayout()
        seed_label = QLabel("Seed:")
        seed_label.setMinimumWidth(50)
        seed_layout.addWidget(seed_label)
        
        self.seed_input = QLineEdit()
        self.seed_input.setText("42")
        self.seed_input.setValidator(QIntValidator(0, 999999999))
        self.seed_input.setPlaceholderText("Enter random seed (integer)")
        seed_layout.addWidget(self.seed_input)
        
        layout.addLayout(seed_layout)
        
        # Run button
        self.run_btn = QPushButton("Run Simulation")
        self.run_btn.clicked.connect(self.run_simulation)
        self.run_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")
        layout.addWidget(self.run_btn)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
    
    def refresh_scenarios(self):
        """Refresh the scenario list from the scenarios directory."""
        self.scenario_list.clear()
        scenarios = find_scenario_files()
        
        if not scenarios:
            self.status_label.setText(f"Status: No scenarios found in {SCENARIOS_DIR}/")
            self.status_label.setStyleSheet("color: orange;")
            return
        
        for filename, full_path in scenarios:
            self.scenario_list.addItem(filename)
            # Store full path in item data
            item = self.scenario_list.item(self.scenario_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
        
        self.status_label.setText(f"Status: Found {len(scenarios)} scenario(s)")
        self.status_label.setStyleSheet("color: green;")
        # Select the first item if the list is not empty
        if self.scenario_list.count() > 0:
            self.scenario_list.setCurrentItem(self.scenario_list.item(0))
            self.on_scenario_selected(self.scenario_list.item(0))
    
    def on_scenario_selected(self, item):
        """Handle scenario selection."""
        self.selected_scenario = item.data(Qt.ItemDataRole.UserRole)
        self.status_label.setText(f"Status: Selected {item.text()}")
        self.status_label.setStyleSheet("color: blue;")
    
    def open_scenario_builder(self):
        """Open the scenario builder dialog."""
        dialog = ScenarioBuilderDialog(self)
        if dialog.exec():
            # Scenario was created, refresh the list
            self.refresh_scenarios()
            
            # Auto-select the new scenario if it was saved in scenarios/
            new_file_path = dialog.saved_path
            if new_file_path:
                # Find item by matching the full path stored in UserRole
                for i in range(self.scenario_list.count()):
                    item = self.scenario_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == str(new_file_path):
                        self.scenario_list.setCurrentItem(item)
                        self.on_scenario_selected(item)
                        break
    
    def run_simulation(self):
        """Run the selected simulation."""
        # Validate selection
        if not self.selected_scenario:
            QMessageBox.warning(
                self,
                "No Scenario Selected",
                "Please select a scenario from the list before running."
            )
            return
        
        # Validate seed
        seed_text = self.seed_input.text().strip()
        if not seed_text:
            QMessageBox.warning(
                self,
                "Invalid Seed",
                "Please enter a valid integer seed."
            )
            return
        
        try:
            seed = int(seed_text)
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Seed",
                "Seed must be an integer."
            )
            return
        
        # Launch simulation
        self.status_label.setText(f"Status: Launching simulation...")
        self.status_label.setStyleSheet("color: blue;")
        QApplication.processEvents()  # Update UI
        
        try:
            # Launch simulation using subprocess
            import subprocess
            import sys
            
            # Use subprocess to run main.py with scenario and seed
            subprocess.Popen([
                sys.executable,
                "main.py",
                self.selected_scenario,
                "--seed",
                str(seed)
            ])
            
            self.status_label.setText(f"Status: Simulation launched")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Launch Error",
                f"Failed to launch simulation:\n{str(e)}"
            )
            self.status_label.setText(f"Status: Error - {str(e)}")
            self.status_label.setStyleSheet("color: red;")
    
    def quit_application(self):
        """Quit the application cleanly."""
        self.close()
        QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event to ensure proper cleanup."""
        # Accept the close event
        event.accept()
        # Ensure the application quits
        QApplication.quit()


def main():
    """Entry point for the launcher."""
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

