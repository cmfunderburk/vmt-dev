"""
Timeline widget for scrubbing through simulation ticks.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSlider, QLabel,
    QPushButton, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class TimelineWidget(QWidget):
    """Widget for navigating through simulation time."""
    
    tick_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.min_tick = 0
        self.max_tick = 0
        self.current_tick = 0
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Timeline")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Slider and controls
        controls_layout = QHBoxLayout()
        
        # Previous button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setMaximumWidth(40)
        self.prev_btn.clicked.connect(self.prev_tick)
        controls_layout.addWidget(self.prev_btn)
        
        # Play/pause button (for future animation)
        self.play_btn = QPushButton("▶")
        self.play_btn.setMaximumWidth(40)
        self.play_btn.setEnabled(False)  # Not implemented yet
        controls_layout.addWidget(self.play_btn)
        
        # Next button
        self.next_btn = QPushButton("▶▶")
        self.next_btn.setMaximumWidth(40)
        self.next_btn.clicked.connect(self.next_tick)
        controls_layout.addWidget(self.next_btn)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_changed)
        controls_layout.addWidget(self.slider, stretch=1)
        
        # Tick spinbox
        self.tick_spinbox = QSpinBox()
        self.tick_spinbox.setMinimum(0)
        self.tick_spinbox.setMaximum(100)
        self.tick_spinbox.setPrefix("Tick: ")
        self.tick_spinbox.valueChanged.connect(self.on_spinbox_changed)
        controls_layout.addWidget(self.tick_spinbox)
        
        layout.addLayout(controls_layout)
        
        # Range label
        self.range_label = QLabel("Range: 0 - 0")
        self.range_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.range_label)
    
    def set_range(self, min_tick: int, max_tick: int):
        """Set the tick range."""
        self.min_tick = min_tick
        self.max_tick = max_tick
        
        self.slider.setMinimum(min_tick)
        self.slider.setMaximum(max_tick)
        self.tick_spinbox.setMinimum(min_tick)
        self.tick_spinbox.setMaximum(max_tick)
        
        self.range_label.setText(f"Range: {min_tick} - {max_tick}")
    
    def set_tick(self, tick: int):
        """Set current tick (programmatically)."""
        if self.min_tick <= tick <= self.max_tick:
            self.current_tick = tick
            self.slider.blockSignals(True)
            self.tick_spinbox.blockSignals(True)
            self.slider.setValue(tick)
            self.tick_spinbox.setValue(tick)
            self.slider.blockSignals(False)
            self.tick_spinbox.blockSignals(False)
    
    def on_slider_changed(self, value: int):
        """Handle slider value change."""
        self.current_tick = value
        self.tick_spinbox.blockSignals(True)
        self.tick_spinbox.setValue(value)
        self.tick_spinbox.blockSignals(False)
        self.tick_changed.emit(value)
    
    def on_spinbox_changed(self, value: int):
        """Handle spinbox value change."""
        self.current_tick = value
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.tick_changed.emit(value)
    
    def prev_tick(self):
        """Go to previous tick."""
        if self.current_tick > self.min_tick:
            self.set_tick(self.current_tick - 1)
            self.tick_changed.emit(self.current_tick)
    
    def next_tick(self):
        """Go to next tick."""
        if self.current_tick < self.max_tick:
            self.set_tick(self.current_tick + 1)
            self.tick_changed.emit(self.current_tick)

