"""
Main log viewer window for analyzing simulation data.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTabWidget, QTableWidget,
    QTableWidgetItem, QSplitter, QMessageBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from telemetry.database import TelemetryDatabase
from .queries import QueryBuilder
from .widgets import TimelineWidget, AgentViewWidget, TradeViewWidget, FilterWidget


class LogViewerWindow(QMainWindow):
    """Main window for log viewer application."""
    
    def __init__(self):
        super().__init__()
        self.db: TelemetryDatabase | None = None
        self.current_run_id: int | None = None
        self.current_tick: int = 0
        self.min_tick: int = 0
        self.max_tick: int = 0
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("VMT Log Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Top controls
        layout.addWidget(self._create_top_controls())
        
        # Run info display
        self.run_info_label = QLabel("No database loaded")
        self.run_info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.run_info_label)
        
        # Timeline widget
        self.timeline = TimelineWidget()
        self.timeline.tick_changed.connect(self.on_tick_changed)
        layout.addWidget(self.timeline)
        
        # Main content area - tabbed interface
        self.tabs = QTabWidget()
        
        # Overview tab
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Agents tab
        self.agent_view = AgentViewWidget()
        self.agent_view.agent_selected.connect(self.on_agent_selected)
        self.tabs.addTab(self.agent_view, "Agents")
        
        # Trades tab
        self.trade_view = TradeViewWidget()
        self.tabs.addTab(self.trade_view, "Trades")
        
        # Decisions tab
        self.decisions_table = QTableWidget()
        self.tabs.addTab(self.decisions_table, "Decisions")
        
        # Resources tab
        self.resources_table = QTableWidget()
        self.tabs.addTab(self.resources_table, "Resources")
        
        # Money tab (WP3 Part 3B)
        self.money_tab = self._create_money_tab()
        self.tabs.addTab(self.money_tab, "Money")
        
        layout.addWidget(self.tabs, stretch=1)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def _create_top_controls(self) -> QWidget:
        """Create top control bar."""
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # Open database button
        self.open_btn = QPushButton("Open Database")
        self.open_btn.clicked.connect(self.open_database)
        layout.addWidget(self.open_btn)
        
        # Run selector
        layout.addWidget(QLabel("Run:"))
        self.run_selector = QComboBox()
        self.run_selector.currentIndexChanged.connect(self.on_run_selected)
        layout.addWidget(self.run_selector)
        
        # Export button
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        layout.addStretch()
        
        # Current tick display
        self.tick_label = QLabel("Tick: --")
        font = QFont()
        font.setBold(True)
        self.tick_label.setFont(font)
        layout.addWidget(self.tick_label)
        
        return widget
    
    def _create_overview_tab(self) -> QWidget:
        """Create overview tab with summary statistics."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Statistics group
        stats_group = QGroupBox("Simulation Statistics")
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)
        
        self.stats_label = QLabel("No data loaded")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # Trade statistics group
        trade_stats_group = QGroupBox("Trade Statistics")
        trade_stats_layout = QVBoxLayout()
        trade_stats_group.setLayout(trade_stats_layout)
        
        self.trade_stats_label = QLabel("No data loaded")
        trade_stats_layout.addWidget(self.trade_stats_label)
        
        layout.addWidget(trade_stats_group)
        
        # Agent trade counts table
        agent_trades_group = QGroupBox("Agent Trade Counts")
        agent_trades_layout = QVBoxLayout()
        agent_trades_group.setLayout(agent_trades_layout)
        
        self.agent_trades_table = QTableWidget()
        self.agent_trades_table.setColumnCount(2)
        self.agent_trades_table.setHorizontalHeaderLabels(["Agent ID", "Trade Count"])
        agent_trades_layout.addWidget(self.agent_trades_table)
        
        layout.addWidget(agent_trades_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_money_tab(self) -> QWidget:
        """Create money analysis tab (WP3 Part 3B)."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Money statistics group
        money_stats_group = QGroupBox("Money Statistics")
        money_stats_layout = QVBoxLayout()
        money_stats_group.setLayout(money_stats_layout)
        
        self.money_stats_label = QLabel("No data loaded")
        money_stats_layout.addWidget(self.money_stats_label)
        
        layout.addWidget(money_stats_group)
        
        # Trade distribution by type
        trade_dist_group = QGroupBox("Trade Distribution by Exchange Pair Type")
        trade_dist_layout = QVBoxLayout()
        trade_dist_group.setLayout(trade_dist_layout)
        
        self.trade_dist_table = QTableWidget()
        self.trade_dist_table.setColumnCount(3)
        self.trade_dist_table.setHorizontalHeaderLabels(["Exchange Pair", "Count", "Percentage"])
        trade_dist_layout.addWidget(self.trade_dist_table)
        
        layout.addWidget(trade_dist_group)
        
        # Money trades table
        money_trades_group = QGroupBox("Money Trades (dM != 0)")
        money_trades_layout = QVBoxLayout()
        money_trades_group.setLayout(money_trades_layout)
        
        self.money_trades_table = QTableWidget()
        money_trades_layout.addWidget(self.money_trades_table)
        
        layout.addWidget(money_trades_group)
        
        return widget
    
    def open_database(self):
        """Open a telemetry database file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Telemetry Database",
            "./logs",
            "Database Files (*.db);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Close existing database
            if self.db:
                self.db.close()
            
            # Open new database
            self.db = TelemetryDatabase(file_path)
            self.load_runs()
            self.statusBar().showMessage(f"Loaded: {Path(file_path).name}")
            self.export_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open database:\n{str(e)}")
    
    def load_runs(self):
        """Load available runs from database."""
        if not self.db:
            return
        
        self.run_selector.clear()
        runs = self.db.get_runs()
        
        for run in runs:
            label = f"Run {run['run_id']}: {run['scenario_name']} ({run['num_agents']} agents)"
            self.run_selector.addItem(label, run['run_id'])
        
        if self.run_selector.count() > 0:
            self.run_selector.setCurrentIndex(0)
    
    def on_run_selected(self, index: int):
        """Handle run selection change."""
        if index < 0 or not self.db:
            return
        
        self.current_run_id = self.run_selector.itemData(index)
        if self.current_run_id is None:
            return
        
        # Load run info
        run_info = self.db.get_run_info(self.current_run_id)
        if run_info:
            info_text = (
                f"Run {run_info['run_id']}: {run_info['scenario_name']} | "
                f"Agents: {run_info['num_agents']} | "
                f"Grid: {run_info['grid_width']}x{run_info['grid_height']} | "
                f"Ticks: {run_info['total_ticks'] or 'In Progress'}"
            )
            self.run_info_label.setText(info_text)
        
        # Get tick range
        query, params = QueryBuilder.get_tick_range(self.current_run_id)
        result = self.db.execute(query, params).fetchone()
        
        if result and result['min_tick'] is not None:
            self.min_tick = result['min_tick']
            self.max_tick = result['max_tick']
            self.timeline.set_range(self.min_tick, self.max_tick)
            self.timeline.set_tick(self.min_tick)
            self.current_tick = self.min_tick
        
        # Load overview statistics
        self.load_overview()
        
        # Load money tab data
        self.load_money_tab()
        
        # Initialize agent view
        self.agent_view.load_run(self.db, self.current_run_id)
    
    def load_overview(self):
        """Load overview statistics."""
        if not self.db or self.current_run_id is None:
            return
        
        # Get run info
        run_info = self.db.get_run_info(self.current_run_id)
        if run_info:
            stats_text = f"""
<b>Scenario:</b> {run_info['scenario_name']}<br>
<b>Number of Agents:</b> {run_info['num_agents']}<br>
<b>Grid Size:</b> {run_info['grid_width']} x {run_info['grid_height']}<br>
<b>Total Ticks:</b> {run_info['total_ticks'] or 'In Progress'}<br>
<b>Start Time:</b> {run_info['start_time']}<br>
<b>End Time:</b> {run_info['end_time'] or 'In Progress'}
"""
            self.stats_label.setText(stats_text)
        
        # Get trade statistics
        query, params = QueryBuilder.get_trade_statistics(self.current_run_id)
        result = self.db.execute(query, params).fetchone()
        
        if result and result['total_trades']:
            trade_stats = f"""
<b>Total Trades:</b> {result['total_trades']}<br>
<b>Average dA:</b> {result['avg_dA']:.2f}<br>
<b>Average dB:</b> {result['avg_dB']:.2f}<br>
<b>Average Price:</b> {result['avg_price']:.4f}<br>
<b>First Trade:</b> Tick {result['first_trade_tick']}<br>
<b>Last Trade:</b> Tick {result['last_trade_tick']}
"""
            self.trade_stats_label.setText(trade_stats)
        else:
            self.trade_stats_label.setText("No trades recorded")
        
        # Get agent trade counts
        query, params = QueryBuilder.get_agent_trade_count(self.current_run_id)
        results = self.db.execute(query, params).fetchall()
        
        self.agent_trades_table.setRowCount(len(results))
        for i, row in enumerate(results):
            self.agent_trades_table.setItem(i, 0, QTableWidgetItem(str(row['agent_id'])))
            self.agent_trades_table.setItem(i, 1, QTableWidgetItem(str(row['trade_count'])))
        
        self.agent_trades_table.resizeColumnsToContents()
    
    def load_money_tab(self):
        """Load money tab data (WP3 Part 3B)."""
        if not self.db or self.current_run_id is None:
            return
        
        # Get money statistics
        query, params = QueryBuilder.get_money_statistics(self.current_run_id)
        result = self.db.execute(query, params).fetchone()
        
        if result and result['money_trades'] and result['money_trades'] > 0:
            avg_buyer_lambda = result['avg_buyer_lambda']
            avg_seller_lambda = result['avg_seller_lambda']

            avg_buyer_lambda_text = (
                f"{avg_buyer_lambda:.4f}" if avg_buyer_lambda is not None else "N/A"
            )
            avg_seller_lambda_text = (
                f"{avg_seller_lambda:.4f}" if avg_seller_lambda is not None else "N/A"
            )

            money_stats = f"""
<b>Monetary Trades:</b> {result['money_trades']}<br>
<b>Average dM:</b> {result['avg_dM']:.2f}<br>
<b>Min dM:</b> {result['min_dM']}<br>
<b>Max dM:</b> {result['max_dM']}<br>
<b>Average Buyer λ:</b> {avg_buyer_lambda_text}<br>
<b>Average Seller λ:</b> {avg_seller_lambda_text}
"""
            self.money_stats_label.setText(money_stats)
        else:
            self.money_stats_label.setText("No monetary trades recorded")
        
        # Get trade distribution by type
        query, params = QueryBuilder.get_trade_distribution_by_type(self.current_run_id)
        results = self.db.execute(query, params).fetchall()
        
        total_trades = sum(row['count'] for row in results)
        
        self.trade_dist_table.setRowCount(len(results))
        for i, row in enumerate(results):
            pair_type = row['exchange_pair_type']
            count = row['count']
            percentage = (count / total_trades * 100) if total_trades > 0 else 0
            
            self.trade_dist_table.setItem(i, 0, QTableWidgetItem(pair_type))
            self.trade_dist_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.trade_dist_table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))
        
        self.trade_dist_table.resizeColumnsToContents()
        
        # Get money trades
        query, params = QueryBuilder.get_money_trades(self.current_run_id)
        results = self.db.execute(query, params).fetchall()
        
        columns = ['tick', 'buyer_id', 'seller_id', 'dA', 'dB', 'dM', 'price', 
                   'buyer_lambda', 'seller_lambda', 'exchange_pair_type']
        
        self.money_trades_table.setColumnCount(len(columns))
        self.money_trades_table.setHorizontalHeaderLabels(columns)
        self.money_trades_table.setRowCount(len(results))
        
        for i, row in enumerate(results):
            for j, col in enumerate(columns):
                value = row[col]
                if value is None:
                    value = ""
                elif isinstance(value, float):
                    value = f"{value:.4f}"
                self.money_trades_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        self.money_trades_table.resizeColumnsToContents()
    
    def on_tick_changed(self, tick: int):
        """Handle timeline tick change."""
        self.current_tick = tick
        self.tick_label.setText(f"Tick: {tick}")
        
        # Update all views
        self.update_views()
    
    def update_views(self):
        """Update all data views for current tick."""
        if not self.db or self.current_run_id is None:
            return
        
        # Update agent view
        self.agent_view.update_tick(self.current_tick)
        
        # Update trade view
        self.trade_view.load_trades(self.db, self.current_run_id, self.current_tick)
        
        # Update decisions
        self.update_decisions_table()
        
        # Update resources
        self.update_resources_table()
    
    def update_decisions_table(self):
        """Update decisions table for current tick."""
        if not self.db or self.current_run_id is None:
            return
        
        query, params = QueryBuilder.get_decisions_at_tick(self.current_run_id, self.current_tick)
        results = self.db.execute(query, params).fetchall()
        
        columns = ['agent_id', 'chosen_partner_id', 'surplus_with_partner', 
                   'target_type', 'target_x', 'target_y', 'num_neighbors']
        
        self.decisions_table.setColumnCount(len(columns))
        self.decisions_table.setHorizontalHeaderLabels(columns)
        self.decisions_table.setRowCount(len(results))
        
        for i, row in enumerate(results):
            for j, col in enumerate(columns):
                value = row[col]
                if value is None:
                    value = ""
                elif isinstance(value, float):
                    value = f"{value:.4f}"
                self.decisions_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        self.decisions_table.resizeColumnsToContents()
    
    def update_resources_table(self):
        """Update resources table for current tick."""
        if not self.db or self.current_run_id is None:
            return
        
        query, params = QueryBuilder.get_resource_state_at_tick(self.current_run_id, self.current_tick)
        results = self.db.execute(query, params).fetchall()
        
        columns = ['x', 'y', 'resource_type', 'amount']
        
        self.resources_table.setColumnCount(len(columns))
        self.resources_table.setHorizontalHeaderLabels(columns)
        self.resources_table.setRowCount(len(results))
        
        for i, row in enumerate(results):
            for j, col in enumerate(columns):
                self.resources_table.setItem(i, j, QTableWidgetItem(str(row[col])))
        
        self.resources_table.resizeColumnsToContents()
    
    def on_agent_selected(self, agent_id: int):
        """Handle agent selection."""
        # Could switch to agent detail view or highlight in other tabs
        self.statusBar().showMessage(f"Selected agent {agent_id}")
    
    def export_to_csv(self):
        """Export current run to CSV files."""
        if not self.db or self.current_run_id is None:
            QMessageBox.warning(self, "Warning", "No run selected")
            return
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            "./logs"
        )
        
        if not directory:
            return
        
        try:
            from .csv_export import export_run_to_csv
            export_run_to_csv(self.db, self.current_run_id, directory)
            QMessageBox.information(self, "Success", f"Exported to {directory}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.db:
            self.db.close()
        event.accept()


def main():
    """Run the log viewer application."""
    app = QApplication(sys.argv)
    viewer = LogViewerWindow()
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

