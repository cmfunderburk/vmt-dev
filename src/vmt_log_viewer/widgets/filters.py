"""
Filter widget for querying simulation data.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QGroupBox
)
from PyQt6.QtCore import pyqtSignal


class FilterWidget(QWidget):
    """Widget for filtering and querying log data."""
    
    filter_applied = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tick range filter
        tick_group = QGroupBox("Tick Range")
        tick_layout = QHBoxLayout()
        tick_group.setLayout(tick_layout)
        
        tick_layout.addWidget(QLabel("From:"))
        self.tick_from = QLineEdit()
        self.tick_from.setPlaceholderText("Start tick")
        tick_layout.addWidget(self.tick_from)
        
        tick_layout.addWidget(QLabel("To:"))
        self.tick_to = QLineEdit()
        self.tick_to.setPlaceholderText("End tick")
        tick_layout.addWidget(self.tick_to)
        
        layout.addWidget(tick_group)
        
        # Agent filter
        agent_group = QGroupBox("Agent")
        agent_layout = QHBoxLayout()
        agent_group.setLayout(agent_layout)
        
        agent_layout.addWidget(QLabel("Agent ID:"))
        self.agent_id = QLineEdit()
        self.agent_id.setPlaceholderText("Agent ID or 'all'")
        agent_layout.addWidget(self.agent_id)
        
        layout.addWidget(agent_group)
        
        # Trade filter
        trade_group = QGroupBox("Trade Filters")
        trade_layout = QVBoxLayout()
        trade_group.setLayout(trade_layout)
        
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        self.direction = QComboBox()
        self.direction.addItems(["All", "i_buys_A", "j_buys_A"])
        direction_layout.addWidget(self.direction)
        trade_layout.addLayout(direction_layout)
        
        layout.addWidget(trade_group)
        
        # Apply button
        self.apply_btn = QPushButton("Apply Filters")
        self.apply_btn.clicked.connect(self.apply_filters)
        layout.addWidget(self.apply_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear Filters")
        self.clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(self.clear_btn)
        
        layout.addStretch()
    
    def apply_filters(self):
        """Apply current filter settings."""
        filters = {
            'tick_from': self.tick_from.text(),
            'tick_to': self.tick_to.text(),
            'agent_id': self.agent_id.text(),
            'direction': self.direction.currentText() if self.direction.currentText() != "All" else None,
        }
        self.filter_applied.emit(filters)
    
    def clear_filters(self):
        """Clear all filter fields."""
        self.tick_from.clear()
        self.tick_to.clear()
        self.agent_id.clear()
        self.direction.setCurrentIndex(0)

