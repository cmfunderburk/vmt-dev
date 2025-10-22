"""
Scenario builder dialog for creating custom scenarios.
"""

import yaml
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QLineEdit, QFormLayout, QScrollArea,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QSlider,
    QGroupBox, QTextBrowser, QSplitter
)
from PyQt6.QtCore import Qt
from .validator import ScenarioValidator, ValidationError

# Default directory to save scenarios
DEFAULT_SCENARIO_DIR = Path("scenarios")

class ScenarioBuilderDialog(QDialog):
    """Dialog for building custom scenarios."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.saved_path = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Create Custom Scenario")
        self.setGeometry(150, 150, 700, 700)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_basic_tab()
        self.create_params_tab()
        self.create_resources_tab()
        self.create_utilities_tab()
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.generate_btn = QPushButton("Generate Scenario")
        self.generate_btn.clicked.connect(self.generate_scenario)
        self.generate_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
    
    def create_basic_tab(self):
        """Create the basic settings tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # Scenario name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my_custom_scenario")
        layout.addRow("Scenario Name*:", self.name_input)
        
        # Grid size
        self.grid_size_input = QSpinBox()
        self.grid_size_input.setRange(5, 200)
        self.grid_size_input.setValue(20)
        layout.addRow("Grid Size (N)*:", self.grid_size_input)
        
        # Number of agents
        self.n_agents_input = QSpinBox()
        self.n_agents_input.setRange(1, 1000)
        self.n_agents_input.setValue(3)
        layout.addRow("Number of Agents*:", self.n_agents_input)
        
        # Initial inventory A
        self.inv_a_input = QLineEdit()
        self.inv_a_input.setText("10")
        self.inv_a_input.setPlaceholderText("10 or 10,20,30")
        self.inv_a_input.setToolTip("Single value or comma-separated list")
        layout.addRow("Initial Inventory A*:", self.inv_a_input)
        
        # Initial inventory B
        self.inv_b_input = QLineEdit()
        self.inv_b_input.setText("10")
        self.inv_b_input.setPlaceholderText("10 or 10,20,30")
        self.inv_b_input.setToolTip("Single value or comma-separated list")
        layout.addRow("Initial Inventory B*:", self.inv_b_input)
        
        self.tabs.addTab(scroll, "Basic Settings")
    
    def create_params_tab(self):
        """Create the simulation parameters tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # Spread
        self.spread_input = QDoubleSpinBox()
        self.spread_input.setRange(0.0, 1.0)
        self.spread_input.setDecimals(3)
        self.spread_input.setSingleStep(0.01)
        self.spread_input.setValue(0.1)
        layout.addRow("Spread:", self.spread_input)
        
        # Vision radius
        self.vision_radius_input = QSpinBox()
        self.vision_radius_input.setRange(0, 50)
        self.vision_radius_input.setValue(5)
        layout.addRow("Vision Radius:", self.vision_radius_input)
        
        # Interaction radius
        self.interaction_radius_input = QSpinBox()
        self.interaction_radius_input.setRange(0, 50)
        self.interaction_radius_input.setValue(2)
        layout.addRow("Interaction Radius:", self.interaction_radius_input)
        
        # Move budget per tick
        self.move_budget_input = QSpinBox()
        self.move_budget_input.setRange(1, 20)
        self.move_budget_input.setValue(1)
        layout.addRow("Move Budget Per Tick:", self.move_budget_input)
        
        # dA_max
        self.delta_a_max_input = QSpinBox()
        self.delta_a_max_input.setRange(1, 100)
        self.delta_a_max_input.setValue(5)
        layout.addRow("dA_max (Max trade size):", self.delta_a_max_input)
        
        # Forage rate
        self.forage_rate_input = QSpinBox()
        self.forage_rate_input.setRange(1, 20)
        self.forage_rate_input.setValue(1)
        layout.addRow("Forage Rate:", self.forage_rate_input)
        
        # Epsilon
        self.epsilon_input = QLineEdit()
        self.epsilon_input.setText("1e-12")
        self.epsilon_input.setToolTip("Scientific notation supported (e.g., 1e-12)")
        layout.addRow("Epsilon:", self.epsilon_input)
        
        # Beta
        self.beta_input = QDoubleSpinBox()
        self.beta_input.setRange(0.01, 1.0)
        self.beta_input.setDecimals(3)
        self.beta_input.setSingleStep(0.05)
        self.beta_input.setValue(0.95)
        layout.addRow("Beta (0-1):", self.beta_input)
        
        # Trade cooldown ticks
        self.trade_cooldown_input = QSpinBox()
        self.trade_cooldown_input.setRange(0, 100)
        self.trade_cooldown_input.setValue(5)
        layout.addRow("Trade Cooldown Ticks:", self.trade_cooldown_input)
        
        self.tabs.addTab(scroll, "Simulation Parameters")
    
    def create_resources_tab(self):
        """Create the resources tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # Resource density with slider
        density_layout = QHBoxLayout()
        self.density_slider = QSlider(Qt.Orientation.Horizontal)
        self.density_slider.setRange(0, 100)
        self.density_slider.setValue(10)
        self.density_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.density_slider.setTickInterval(10)
        self.density_label = QLabel("0.10")
        self.density_slider.valueChanged.connect(
            lambda v: self.density_label.setText(f"{v/100:.2f}")
        )
        density_layout.addWidget(self.density_slider)
        density_layout.addWidget(self.density_label)
        layout.addRow("Resource Density (0-1):", density_layout)
        
        # Resource amount
        self.resource_amount_input = QSpinBox()
        self.resource_amount_input.setRange(1, 100)
        self.resource_amount_input.setValue(10)
        layout.addRow("Resource Amount:", self.resource_amount_input)
        
        # Resource growth rate
        self.resource_growth_input = QSpinBox()
        self.resource_growth_input.setRange(0, 20)
        self.resource_growth_input.setValue(1)
        self.resource_growth_input.setToolTip("0 = no regeneration")
        layout.addRow("Resource Growth Rate:", self.resource_growth_input)
        
        # Resource max amount
        self.resource_max_input = QSpinBox()
        self.resource_max_input.setRange(1, 100)
        self.resource_max_input.setValue(10)
        layout.addRow("Resource Max Amount:", self.resource_max_input)
        
        # Resource regen cooldown
        self.resource_cooldown_input = QSpinBox()
        self.resource_cooldown_input.setRange(0, 100)
        self.resource_cooldown_input.setValue(5)
        layout.addRow("Resource Regen Cooldown:", self.resource_cooldown_input)
        
        self.tabs.addTab(scroll, "Resources")
    
    def create_utilities_tab(self):
        """Create the utilities tab with documentation panel."""
        tab = QWidget()
        main_layout = QHBoxLayout()
        tab.setLayout(main_layout)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - utility configuration
        left_widget = QWidget()
        layout = QVBoxLayout()
        left_widget.setLayout(layout)
        
        # Instructions
        instructions = QLabel("Define utility functions for agents. Weights must sum to 1.0.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Utility table
        self.utilities_table = QTableWidget()
        self.utilities_table.setColumnCount(5)
        self.utilities_table.setHorizontalHeaderLabels([
            "Type", "Weight", "Param 1", "Param 2", "Param 3"
        ])
        self.utilities_table.setRowCount(1)
        
        # Add default CES utility
        self.add_utility_row(0, "ces", 1.0, 0.5, 1.0, 1.0)
        
        layout.addWidget(self.utilities_table)
        
        # Utility buttons
        button_layout = QHBoxLayout()
        
        add_utility_btn = QPushButton("Add Utility")
        add_utility_btn.clicked.connect(self.add_utility)
        button_layout.addWidget(add_utility_btn)
        
        remove_utility_btn = QPushButton("Remove Selected")
        remove_utility_btn.clicked.connect(self.remove_utility)
        button_layout.addWidget(remove_utility_btn)
        
        button_layout.addStretch()
        
        self.normalize_checkbox = QCheckBox("Auto-normalize weights")
        self.normalize_checkbox.setChecked(True)
        button_layout.addWidget(self.normalize_checkbox)
        
        layout.addLayout(button_layout)
        
        # Help text
        help_text = QLabel(
            "<b>CES Utility:</b> Param1=rho, Param2=wA, Param3=wB<br>"
            "<b>Linear Utility:</b> Param1=vA, Param2=vB, Param3=unused"
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        splitter.addWidget(left_widget)
        
        # Right panel - documentation
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        doc_label = QLabel("<b>Utility Function Documentation</b>")
        doc_label.setStyleSheet("font-size: 14px; padding: 5px;")
        right_layout.addWidget(doc_label)
        
        # Documentation text browser
        self.utility_docs = QTextBrowser()
        self.utility_docs.setOpenExternalLinks(False)
        self.utility_docs.setHtml(self.get_utility_documentation())
        right_layout.addWidget(self.utility_docs)
        
        splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (60% left, 40% right)
        splitter.setSizes([400, 300])
        
        self.tabs.addTab(tab, "Utility Functions")
    
    def get_utility_documentation(self):
        """Generate HTML documentation for utility functions."""
        return """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; font-size: 11px; }
                h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 15px; }
                h3 { color: #34495e; margin-top: 12px; margin-bottom: 5px; }
                .param { background-color: #ecf0f1; padding: 8px; margin: 5px 0; border-radius: 4px; }
                .param-name { font-weight: bold; color: #2980b9; }
                .behavior { background-color: #e8f5e9; padding: 8px; margin: 8px 0; border-left: 4px solid #4caf50; }
                .warning { background-color: #fff3cd; padding: 8px; margin: 8px 0; border-left: 4px solid #ffc107; }
                .formula { font-family: 'Courier New', monospace; background-color: #f8f9fa; padding: 5px; margin: 5px 0; }
                ul { margin: 5px 0; padding-left: 20px; }
                li { margin: 3px 0; }
            </style>
        </head>
        <body>
            <h2>CES Utility Function</h2>
            
            <div class="formula">
                U(A, B) = [wA × A<sup>ρ</sup> + wB × B<sup>ρ</sup>]<sup>1/ρ</sup>
            </div>
            
            <div class="behavior">
                <strong>Best for:</strong> Modeling agents with varying degrees of substitutability between goods. 
                CES allows you to control how willing agents are to substitute one good for another, 
                making it ideal for realistic economic behavior where goods may be complements or substitutes.
            </div>
            
            <h3>Parameters</h3>
            
            <div class="param">
                <span class="param-name">Param 1: ρ (rho)</span> - Elasticity of substitution parameter
                <ul>
                    <li><strong>ρ &lt; 0:</strong> Goods are <strong>complements</strong> - agents need both goods together. 
                    Having only one good provides little utility. Example: Left and right shoes.</li>
                    
                    <li><strong>ρ → 0:</strong> Approaches <strong>Cobb-Douglas</strong> preferences - balanced desire for both goods. 
                    Agents maintain relatively constant ratios.</li>
                    
                    <li><strong>0 &lt; ρ &lt; 1:</strong> <strong>Weak substitutes</strong> - goods can replace each other but not perfectly. 
                    Agents prefer variety but will accept imbalanced bundles.</li>
                    
                    <li><strong>ρ → 1:</strong> Approaches <strong>perfect substitutes</strong> - agents treat goods as interchangeable. 
                    Warning: ρ = 1 exactly is not allowed (use Linear utility instead).</li>
                    
                    <li><strong>ρ &gt; 1:</strong> <strong>Strong substitutes</strong> - agents strongly prefer having more of one good 
                    rather than balanced amounts. Can lead to specialization.</li>
                </ul>
            </div>
            
            <div class="param">
                <span class="param-name">Param 2: wA</span> - Weight for good A (must be &gt; 0)
                <ul>
                    <li><strong>Higher wA:</strong> Agent values good A more relative to B. Will demand higher prices when selling A, 
                    and offer higher prices when buying A.</li>
                    
                    <li><strong>wA = wB:</strong> Symmetric preferences - agent treats both goods equally (when starting with equal amounts).</li>
                    
                    <li><strong>wA &lt; wB:</strong> Agent prefers good B. Will trade A more readily to acquire B.</li>
                </ul>
            </div>
            
            <div class="param">
                <span class="param-name">Param 3: wB</span> - Weight for good B (must be &gt; 0)
                <ul>
                    <li><strong>Higher wB:</strong> Agent values good B more relative to A. Will demand higher prices when selling B, 
                    and offer higher prices when buying B.</li>
                    
                    <li><strong>Relative weights matter:</strong> What matters is the ratio wA/wB, not absolute values. 
                    (wA=1, wB=2) behaves the same as (wA=0.5, wB=1).</li>
                </ul>
            </div>
            
            <div class="warning">
                <strong>Common Configurations:</strong><br>
                • <strong>Complementary goods:</strong> ρ = -1, wA = wB = 1<br>
                • <strong>Balanced preferences:</strong> ρ = 0.5, wA = wB = 1<br>
                • <strong>Substitutable goods:</strong> ρ = 0.8, wA = wB = 1<br>
                • <strong>Asymmetric preferences:</strong> ρ = 0.5, wA = 2, wB = 1 (prefers A)
            </div>
            
            <h2>Linear Utility Function</h2>
            
            <div class="formula">
                U(A, B) = vA × A + vB × B
            </div>
            
            <div class="behavior">
                <strong>Best for:</strong> Modeling agents who view goods as perfect substitutes with constant 
                marginal value. Ideal for simple scenarios, money-like goods, or when you want predictable, 
                linear trading behavior. Agents will always trade at a constant rate regardless of inventory levels.
            </div>
            
            <h3>Parameters</h3>
            
            <div class="param">
                <span class="param-name">Param 1: vA</span> - Value per unit of good A (must be &gt; 0)
                <ul>
                    <li><strong>Higher vA:</strong> Each unit of A provides more utility. Agent will be willing to pay 
                    more of good B to acquire A, and will demand more B when selling A.</li>
                    
                    <li><strong>MRS = vA/vB:</strong> The marginal rate of substitution is constant. An agent with 
                    vA=2, vB=1 will always trade 2 units of B for 1 unit of A (or vice versa).</li>
                    
                    <li><strong>Trading behavior:</strong> Agents trade until they cannot improve utility at the 
                    constant exchange rate vA/vB, regardless of current inventory.</li>
                </ul>
            </div>
            
            <div class="param">
                <span class="param-name">Param 2: vB</span> - Value per unit of good B (must be &gt; 0)
                <ul>
                    <li><strong>Higher vB:</strong> Each unit of B provides more utility. Agent will be willing to pay 
                    more of good A to acquire B, and will demand more A when selling B.</li>
                    
                    <li><strong>Price independence:</strong> Unlike CES, linear utility agents don't care about their 
                    current inventory levels - they always value the next unit the same.</li>
                </ul>
            </div>
            
            <div class="param">
                <span class="param-name">Param 3:</span> - <em>Unused for linear utility</em>
            </div>
            
            <div class="warning">
                <strong>Common Configurations:</strong><br>
                • <strong>Equal value:</strong> vA = vB = 1 (trade 1:1 ratio)<br>
                • <strong>A twice as valuable:</strong> vA = 2, vB = 1 (trade 2:1 ratio)<br>
                • <strong>B three times as valuable:</strong> vA = 1, vB = 3 (trade 1:3 ratio)
            </div>
            
            <h2>Defining a Population Mix</h2>
            
            <div class="behavior">
                <strong>Heterogeneous Populations:</strong> You can define multiple utility function templates, each with a `weight`. When the simulation starts, each agent is randomly assigned <strong>one</strong> of these utility functions according to the specified weights. This allows you to create a diverse population of agents with different preferences.
            </div>
            
            <div class="param">
                <span class="param-name">Weight</span> - The probability of an agent being assigned this utility function. All weights must sum to 1.0.
                <ul>
                    <li><strong>Single Type:</strong> To give all agents the same utility function, create one entry with `Weight = 1.0`.</li>
                    <li><strong>Mixed Population:</strong> For a mix of 70% CES and 30% Linear agents, create two entries with weights `0.7` and `0.3` respectively.</li>
                    <li><strong>Auto-normalize:</strong> Check the box to automatically scale the weights you enter so they sum to 1.0. For example, if you enter weights of 3 and 1, they will be normalized to 0.75 and 0.25.</li>
                </ul>
            </div>
            
        </body>
        </html>
        """
    
    def add_utility_row(self, row, utype="ces", weight=0.5, p1=0.5, p2=1.0, p3=1.0):
        """Add a utility row to the table."""
        # Type dropdown
        type_combo = QComboBox()
        type_combo.addItems(["ces", "linear"])
        type_combo.setCurrentText(utype)
        self.utilities_table.setCellWidget(row, 0, type_combo)
        
        # Weight
        weight_item = QTableWidgetItem(str(weight))
        self.utilities_table.setItem(row, 1, weight_item)
        
        # Parameters
        p1_item = QTableWidgetItem(str(p1))
        self.utilities_table.setItem(row, 2, p1_item)
        
        p2_item = QTableWidgetItem(str(p2))
        self.utilities_table.setItem(row, 3, p2_item)
        
        p3_item = QTableWidgetItem(str(p3))
        self.utilities_table.setItem(row, 4, p3_item)
    
    def add_utility(self):
        """Add a new utility row."""
        row = self.utilities_table.rowCount()
        self.utilities_table.insertRow(row)
        self.add_utility_row(row)
    
    def remove_utility(self):
        """Remove selected utility row."""
        current_row = self.utilities_table.currentRow()
        if current_row >= 0:
            if self.utilities_table.rowCount() > 1:
                self.utilities_table.removeRow(current_row)
            else:
                QMessageBox.warning(self, "Cannot Remove", "At least one utility function must remain.")
    
    def collect_data(self):
        """Collect and validate all form data."""
        validator = ScenarioValidator()
        data = {}
        
        try:
            # Basic settings
            data['name'] = validator.validate_string(self.name_input.text(), "Scenario name")
            data['N'] = self.grid_size_input.value()
            data['agents'] = self.n_agents_input.value()
            
            # Parse inventories
            inv_a_text = self.inv_a_input.text().strip()
            inv_b_text = self.inv_b_input.text().strip()
            
            inv_a_list = validator.validate_inventory_list(inv_a_text, "Initial inventory A")
            inv_b_list = validator.validate_inventory_list(inv_b_text, "Initial inventory B")
            
            # Use single value or list
            data['inv_A'] = inv_a_list[0] if len(inv_a_list) == 1 else inv_a_list
            data['inv_B'] = inv_b_list[0] if len(inv_b_list) == 1 else inv_b_list
            
            # Parameters
            data['spread'] = self.spread_input.value()
            data['vision_radius'] = self.vision_radius_input.value()
            data['interaction_radius'] = self.interaction_radius_input.value()
            data['move_budget_per_tick'] = self.move_budget_input.value()
            data['delta_a_max'] = self.delta_a_max_input.value()
            data['forage_rate'] = self.forage_rate_input.value()
            
            # Epsilon (handle scientific notation)
            epsilon_text = self.epsilon_input.text().strip()
            data['epsilon'] = validator.validate_positive_float(epsilon_text, "Epsilon")
            
            data['beta'] = self.beta_input.value()
            data['trade_cooldown_ticks'] = self.trade_cooldown_input.value()
            
            # Resources
            data['resource_density'] = self.density_slider.value() / 100.0
            data['resource_amount'] = self.resource_amount_input.value()
            data['resource_growth_rate'] = self.resource_growth_input.value()
            data['resource_max_amount'] = self.resource_max_input.value()
            data['resource_regen_cooldown'] = self.resource_cooldown_input.value()
            
            # Utilities
            utilities = []
            for row in range(self.utilities_table.rowCount()):
                utype = self.utilities_table.cellWidget(row, 0).currentText()
                
                try:
                    weight = float(self.utilities_table.item(row, 1).text())
                    p1 = float(self.utilities_table.item(row, 2).text())
                    p2 = float(self.utilities_table.item(row, 3).text())
                    p3 = float(self.utilities_table.item(row, 4).text())
                except (ValueError, AttributeError):
                    raise ValidationError(f"Invalid values in utility row {row+1}")
                
                if utype == "ces":
                    params = {'rho': p1, 'wA': p2, 'wB': p3}
                    validator.validate_ces_params(params)
                else:  # linear
                    params = {'vA': p1, 'vB': p2}
                    validator.validate_linear_params(params)
                
                utilities.append({
                    'type': utype,
                    'weight': weight,
                    'params': params
                })
            
            # Normalize weights if checkbox is checked
            if self.normalize_checkbox.isChecked():
                total_weight = sum(u['weight'] for u in utilities)
                if total_weight > 0:
                    for u in utilities:
                        u['weight'] /= total_weight
            
            # Validate weights sum to 1.0
            validator.validate_utility_weights(utilities)
            
            data['utilities'] = utilities
            
            return data
            
        except ValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise ValidationError(f"Validation error: {str(e)}")
    
    def generate_yaml(self, data):
        """Generate YAML content from validated data."""
        scenario = {
            'schema_version': 1,
            'name': data['name'],
            'N': data['N'],
            'agents': data['agents'],
            'initial_inventories': {
                'A': data['inv_A'],
                'B': data['inv_B']
            },
            'params': {
                'spread': data['spread'],
                'vision_radius': data['vision_radius'],
                'interaction_radius': data['interaction_radius'],
                'move_budget_per_tick': data['move_budget_per_tick'],
                'dA_max': data['delta_a_max'],
                'forage_rate': data['forage_rate'],
                'epsilon': data['epsilon'],
                'beta': data['beta'],
                'resource_growth_rate': data['resource_growth_rate'],
                'resource_max_amount': data['resource_max_amount'],
                'resource_regen_cooldown': data['resource_regen_cooldown'],
                'trade_cooldown_ticks': data['trade_cooldown_ticks']
            },
            'resource_seed': {
                'density': data['resource_density'],
                'amount': data['resource_amount']
            },
            'utilities': {
                'mix': data['utilities']
            }
        }
        
        # Generate YAML
        yaml_content = yaml.dump(scenario, default_flow_style=False, sort_keys=False)
        
        return yaml_content
    
    def generate_scenario(self):
        """Generate and save the scenario file."""
        try:
            # Collect and validate data
            data = self.collect_data()
            
            # Generate YAML
            yaml_content = self.generate_yaml(data)
            
            # Open save dialog
            default_filename = data['name'].replace(' ', '_').lower() + '.yaml'
            default_path = DEFAULT_SCENARIO_DIR / default_filename
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Scenario File",
                str(default_path),
                "YAML Files (*.yaml);;All Files (*)"
            )
            
            if file_path:
                # Ensure .yaml extension
                if not file_path.endswith('.yaml'):
                    file_path += '.yaml'
                
                # Write file
                with open(file_path, 'w') as f:
                    f.write(yaml_content)
                
                self.saved_path = Path(file_path)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Scenario saved successfully to:\n{file_path}"
                )
                
                # Close dialog with success
                self.accept()
        
        except ValidationError as e:
            QMessageBox.warning(
                self,
                "Validation Error",
                str(e)
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate scenario:\n{str(e)}"
            )

