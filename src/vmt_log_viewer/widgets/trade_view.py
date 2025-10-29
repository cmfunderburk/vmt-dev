"""
Trade view widget for analyzing trades.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..queries import QueryBuilder


class TradeViewWidget(QWidget):
    """Widget for viewing and analyzing trade data."""
    
    def __init__(self):
        super().__init__()
        self.db = None
        self.run_id = None
        self.current_tick = 0
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Trades at current tick
        current_group = QGroupBox("Trades at Current Tick")
        current_layout = QVBoxLayout()
        current_group.setLayout(current_layout)
        
        self.current_trades_table = QTableWidget()
        self.current_trades_table.cellClicked.connect(self.on_trade_clicked)
        current_layout.addWidget(self.current_trades_table)
        
        self.current_trades_summary_label = QLabel("No trades at this tick")
        current_layout.addWidget(self.current_trades_summary_label)
        
        layout.addWidget(current_group)
        
        # Trade details
        details_group = QGroupBox("Trade Details")
        details_layout = QVBoxLayout()
        details_group.setLayout(details_layout)
        
        self.details_label = QLabel("Select a trade to see details")
        details_layout.addWidget(self.details_label)
        
        self.show_attempts_btn = QPushButton("Show Trade Attempts (DEBUG)")
        self.show_attempts_btn.clicked.connect(self.show_trade_attempts)
        self.show_attempts_btn.setEnabled(False)
        details_layout.addWidget(self.show_attempts_btn)
        
        layout.addWidget(details_group)
    
    def load_trades(self, db, run_id: int, tick: int):
        """Load trades for a specific tick."""
        self.db = db
        self.run_id = run_id
        self.current_tick = tick
        
        query, params = QueryBuilder.get_trades_at_tick(run_id, tick)
        results = self.db.execute(query, params).fetchall()
        
        columns = ['buyer_id', 'seller_id', 'x', 'y', 'dA', 'dB', 'dM', 'price', 'direction', 'exchange_pair_type']
        
        self.current_trades_table.setColumnCount(len(columns))
        self.current_trades_table.setHorizontalHeaderLabels(columns)
        self.current_trades_table.setRowCount(len(results))
        
        for i, row in enumerate(results):
            for j, col in enumerate(columns):
                value = row[col]
                if value is None:
                    value = ""
                if isinstance(value, float):
                    value = f"{value:.6f}"
                self.current_trades_table.setItem(i, j, QTableWidgetItem(str(value)))
        
        self.current_trades_table.resizeColumnsToContents()
        
        # Update summary
        if len(results) > 0:
            total_dA = sum(row['dA'] for row in results)
            total_dB = sum(row['dB'] for row in results)
            total_dM = sum(row['dM'] for row in results)
            avg_price = sum(row['price'] for row in results) / len(results)
            summary = (
                f"{len(results)} trades | Total dA: {total_dA} | "
                f"Total dB: {total_dB} | Total dM: {total_dM} | Avg Price: {avg_price:.4f}"
            )
        else:
            summary = "No trades at this tick"
        
        self.current_trades_summary_label.setText(summary)
    
    def on_trade_clicked(self, row: int, col: int):
        """Handle click on trade table."""
        if row < 0:
            return
        
        buyer_id = int(self.current_trades_table.item(row, 0).text())
        seller_id = int(self.current_trades_table.item(row, 1).text())
        dA = int(self.current_trades_table.item(row, 4).text())
        dB = int(self.current_trades_table.item(row, 5).text())
        dM = int(self.current_trades_table.item(row, 6).text())
        price = float(self.current_trades_table.item(row, 7).text())
        direction = self.current_trades_table.item(row, 8).text()
        exchange_pair_type = self.current_trades_table.item(row, 9).text()
        
        details = f"""
<b>Buyer ID:</b> {buyer_id}<br>
<b>Seller ID:</b> {seller_id}<br>
<b>Amount A Traded:</b> {dA}<br>
<b>Amount B Traded:</b> {dB}<br>
<b>Amount M Traded:</b> {dM}<br>
<b>Price:</b> {price:.6f}<br>
<b>Direction:</b> {direction}<br>
<b>Exchange Pair:</b> {exchange_pair_type}<br>
<b>Tick:</b> {self.current_tick}
"""
        self.details_label.setText(details)
        self.show_attempts_btn.setEnabled(True)
        
        # Store selected trade for attempts view
        self.selected_buyer_id = buyer_id
        self.selected_seller_id = seller_id
    
    def show_trade_attempts(self):
        """Show all attempts for the selected trade."""
        if not self.db or self.run_id is None:
            return
        
        if not hasattr(self, 'selected_buyer_id'):
            return
        
        query, params = QueryBuilder.get_trade_attempts_for_trade(
            self.run_id, self.selected_buyer_id, 
            self.selected_seller_id, self.current_tick
        )
        results = self.db.execute(query, params).fetchall()
        
        if not results:
            self.details_label.setText(
                self.details_label.text() + 
                "<br><br><i>No detailed trade attempts recorded (not in DEBUG mode)</i>"
            )
            return
        
        # Display attempts in a dialog or update the details view
        attempts_text = f"<br><br><b>Trade Attempts ({len(results)} iterations):</b><br>"
        for i, row in enumerate(results):
            attempts_text += f"""
<br><i>Attempt {i+1}:</i>
dA={row['dA_attempted']}, dB={row['dB_calculated']}, 
Result={row['result']}, Reason={row['result_reason']}<br>
"""
        
        self.details_label.setText(self.details_label.text() + attempts_text)

