"""
Agent-focused view widget for detailed agent analysis.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QComboBox, QPushButton, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..queries import QueryBuilder


class AgentViewWidget(QWidget):
    """Widget for viewing and analyzing agent data."""
    
    agent_selected = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.db = None
        self.run_id = None
        self.current_tick = 0
        self.selected_agent_id = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Top controls
        controls = QHBoxLayout()
        
        controls.addWidget(QLabel("Agent:"))
        self.agent_selector = QComboBox()
        self.agent_selector.currentIndexChanged.connect(self.on_agent_selected)
        controls.addWidget(self.agent_selector)
        
        self.show_trajectory_btn = QPushButton("Show Trajectory")
        self.show_trajectory_btn.clicked.connect(self.show_trajectory)
        controls.addWidget(self.show_trajectory_btn)
        
        self.show_trades_btn = QPushButton("Show Trades")
        self.show_trades_btn.clicked.connect(self.show_trades)
        controls.addWidget(self.show_trades_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Agent state at current tick
        state_widget = QWidget()
        state_layout = QVBoxLayout()
        state_widget.setLayout(state_layout)
        
        state_title = QLabel("Current State")
        font = QFont()
        font.setBold(True)
        state_title.setFont(font)
        state_layout.addWidget(state_title)
        
        self.state_label = QLabel("No agent selected")
        state_layout.addWidget(self.state_label)
        
        splitter.addWidget(state_widget)
        
        # All agents table
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_widget.setLayout(table_layout)
        
        table_title = QLabel("All Agents at Current Tick")
        table_title.setFont(font)
        table_layout.addWidget(table_title)
        
        self.agents_table = QTableWidget()
        self.agents_table.cellClicked.connect(self.on_table_cell_clicked)
        table_layout.addWidget(self.agents_table)
        
        splitter.addWidget(table_widget)
        
        layout.addWidget(splitter)
    
    def load_run(self, db, run_id: int):
        """Load agent data for a run."""
        self.db = db
        self.run_id = run_id
        
        # Load agent IDs
        query, params = QueryBuilder.get_agent_ids(run_id)
        results = self.db.execute(query, params).fetchall()
        
        self.agent_selector.clear()
        for row in results:
            agent_id = row['agent_id']
            self.agent_selector.addItem(f"Agent {agent_id}", agent_id)
    
    def update_tick(self, tick: int):
        """Update view for new tick."""
        self.current_tick = tick
        
        # Update selected agent state
        if self.selected_agent_id is not None:
            self.update_agent_state()
        
        # Update all agents table
        self.update_agents_table()
    
    def on_agent_selected(self, index: int):
        """Handle agent selection from dropdown."""
        if index >= 0:
            self.selected_agent_id = self.agent_selector.itemData(index)
            self.update_agent_state()
            self.agent_selected.emit(self.selected_agent_id)
    
    def on_table_cell_clicked(self, row: int, col: int):
        """Handle click on agents table."""
        if row >= 0:
            agent_id_item = self.agents_table.item(row, 0)
            if agent_id_item:
                agent_id = int(agent_id_item.text())
                # Update dropdown to match
                for i in range(self.agent_selector.count()):
                    if self.agent_selector.itemData(i) == agent_id:
                        self.agent_selector.setCurrentIndex(i)
                        break
    
    def update_agent_state(self):
        """Update the selected agent's state display."""
        if not self.db or self.run_id is None or self.selected_agent_id is None:
            return
        
        query, params = QueryBuilder.get_agent_snapshot(
            self.run_id, self.selected_agent_id, self.current_tick
        )
        result = self.db.execute(query, params).fetchone()
        
        if result:
            state_text = f"""
<b>Agent ID:</b> {result['agent_id']}<br>
<b>Position:</b> ({result['x']}, {result['y']})<br>
<b>Inventory A:</b> {result['inventory_A']}<br>
<b>Inventory B:</b> {result['inventory_B']}<br>
<b>Utility:</b> {result['utility']:.4f}<br>
<b>Ask (A in B):</b> {result['ask_A_in_B']:.4f}<br>
<b>Bid (A in B):</b> {result['bid_A_in_B']:.4f}<br>
<b>p_min:</b> {result['p_min']:.4f}<br>
<b>p_max:</b> {result['p_max']:.4f}<br>
<b>Utility Type:</b> {result['utility_type']}<br>
"""
            if result['target_agent_id']:
                state_text += f"<b>Target Agent:</b> {result['target_agent_id']}<br>"
            if result['target_x'] is not None:
                state_text += f"<b>Target Position:</b> ({result['target_x']}, {result['target_y']})<br>"
            
            self.state_label.setText(state_text)
        else:
            self.state_label.setText("No data for this tick")
    
    def update_agents_table(self):
        """Update the table showing all agents."""
        if not self.db or self.run_id is None:
            return
        
        query, params = QueryBuilder.get_all_agents_at_tick(self.run_id, self.current_tick)
        results = self.db.execute(query, params).fetchall()
        
        columns = ['agent_id', 'x', 'y', 'inventory_A', 'inventory_B', 
                   'utility', 'ask_A_in_B', 'bid_A_in_B']
        
        self.agents_table.setColumnCount(len(columns))
        self.agents_table.setHorizontalHeaderLabels(columns)
        self.agents_table.setRowCount(len(results))
        
        for i, row in enumerate(results):
            for j, col in enumerate(columns):
                value = row[col]
                if isinstance(value, float):
                    value = f"{value:.4f}"
                self.agents_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        self.agents_table.resizeColumnsToContents()
    
    def show_trajectory(self):
        """Show trajectory for selected agent."""
        if self.selected_agent_id is None:
            return
        
        # This would open a dialog or switch to a visualization
        # For now, just update status
        # TODO: Implement trajectory visualization
        pass
    
    def show_trades(self):
        """Show trades for selected agent."""
        if self.selected_agent_id is None:
            return
        
        # This would filter the trades view
        # TODO: Implement trade filtering
        pass

