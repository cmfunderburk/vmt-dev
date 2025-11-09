# Stage 4: Unified Launcher Implementation

**Purpose**: Create unified interface for all simulation tracks  
**Duration**: Weeks 13-14  
**Prerequisites**: Agent-Based and Game Theory tracks operational

---

## Architecture Overview

```python
# src/vmt_launcher/unified_launcher.py
class UnifiedLauncher(QMainWindow):
    """
    Single entry point for all VMT simulation paradigms
    """
    
    def __init__(self):
        super().__init__()
        self.current_track = None
        self.scenario_manager = ScenarioManager()
        self.launch_manager = LaunchManager()
        self.comparison_tool = ComparisonTool()
        self.init_ui()
```

---

## Week 13: Core Launcher Structure

### Main Window Implementation

```python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QTabWidget,
    QGroupBox, QComboBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

class UnifiedLauncher(QMainWindow):
    """
    Main launcher window with track selection
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VMT: Visualizing Microeconomic Theory")
        self.setMinimumSize(1200, 800)
        
        # Track managers
        self.abm_manager = ABMTrackManager()
        self.gt_manager = GameTheoryManager()
        self.neo_manager = NeoclassicalManager()  # Placeholder
        
        # Shared components
        self.scenario_config = ScenarioConfiguration()
        self.parameter_editor = ParameterEditor()
        self.results_manager = ResultsManager()
        
        self.init_ui()
        self.apply_theme()
    
    def init_ui(self):
        """
        Build the user interface
        """
        # Central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Header section
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Track selection section
        track_selector = self.create_track_selector()
        main_layout.addWidget(track_selector)
        
        # Stacked widget for track-specific content
        self.stacked_widget = QStackedWidget()
        
        # Add track pages
        self.abm_page = self.create_abm_page()
        self.gt_page = self.create_gt_page()
        self.neo_page = self.create_neo_page()
        
        self.stacked_widget.addWidget(self.abm_page)
        self.stacked_widget.addWidget(self.gt_page)
        self.stacked_widget.addWidget(self.neo_page)
        
        main_layout.addWidget(self.stacked_widget)
        
        # Footer with common controls
        footer = self.create_footer()
        main_layout.addWidget(footer)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def create_header(self):
        """
        Create application header with title and description
        """
        header = QWidget()
        layout = QVBoxLayout(header)
        
        # Title
        title = QLabel("Visualizing Microeconomic Theory")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtitle
        subtitle = QLabel("Explore markets through emergence, strategy, and equilibrium")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_font.setItalic(True)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
    
    def create_track_selector(self):
        """
        Create track selection buttons
        """
        selector = QWidget()
        layout = QHBoxLayout(selector)
        
        # Agent-Based button
        self.abm_btn = self.create_track_button(
            "Agent-Based\nSimulation",
            "Emergent market phenomena from individual interactions",
            self.select_abm_track
        )
        
        # Game Theory button
        self.gt_btn = self.create_track_button(
            "Game Theory\nAnalysis",
            "Strategic interactions in small groups",
            self.select_gt_track
        )
        
        # Neoclassical button
        self.neo_btn = self.create_track_button(
            "Neoclassical\nModels",
            "Equilibrium benchmarks and tatonnement",
            self.select_neo_track
        )
        self.neo_btn.setEnabled(False)  # Not yet implemented
        
        layout.addWidget(self.abm_btn)
        layout.addWidget(self.gt_btn)
        layout.addWidget(self.neo_btn)
        
        return selector
    
    def create_track_button(self, title, description, callback):
        """
        Create styled track selection button
        """
        button = QPushButton()
        button.setMinimumHeight(100)
        
        # Create rich text for button
        text = f"<b>{title}</b><br><small>{description}</small>"
        button.setText(text)
        
        # Style
        button.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:1 #e8e8e8);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fff, stop:1 #f0f0f0);
                border-color: #999;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0e0e0, stop:1 #d0d0d0);
            }
            QPushButton:disabled {
                color: #999;
                background: #f0f0f0;
                border-color: #ddd;
            }
        """)
        
        button.clicked.connect(callback)
        return button
```

### Track-Specific Pages

```python
    def create_abm_page(self):
        """
        Create Agent-Based simulation configuration page
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Configuration tabs
        tabs = QTabWidget()
        
        # Scenario tab
        scenario_tab = self.create_abm_scenario_tab()
        tabs.addTab(scenario_tab, "Scenario")
        
        # Protocols tab
        protocols_tab = self.create_abm_protocols_tab()
        tabs.addTab(protocols_tab, "Protocols")
        
        # Parameters tab
        params_tab = self.create_abm_parameters_tab()
        tabs.addTab(params_tab, "Parameters")
        
        # Visualization tab
        viz_tab = self.create_abm_viz_tab()
        tabs.addTab(viz_tab, "Visualization")
        
        layout.addWidget(tabs)
        
        # Launch controls
        controls = self.create_abm_controls()
        layout.addWidget(controls)
        
        return page
    
    def create_abm_scenario_tab(self):
        """
        Scenario selection and configuration for ABM
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scenario selector
        selector_group = QGroupBox("Select Scenario")
        selector_layout = QVBoxLayout(selector_group)
        
        # Dropdown for pre-built scenarios
        self.abm_scenario_combo = QComboBox()
        self.abm_scenario_combo.addItems([
            "Two Agent Trade",
            "Ten Agent Cluster",
            "Hundred Agent Market",
            "Custom Configuration"
        ])
        selector_layout.addWidget(QLabel("Pre-built Scenarios:"))
        selector_layout.addWidget(self.abm_scenario_combo)
        
        # Quick configuration
        quick_config = QGroupBox("Quick Configuration")
        config_layout = QFormLayout(quick_config)
        
        self.abm_agents_spin = QSpinBox()
        self.abm_agents_spin.setRange(2, 1000)
        self.abm_agents_spin.setValue(10)
        config_layout.addRow("Number of Agents:", self.abm_agents_spin)
        
        self.abm_grid_spin = QSpinBox()
        self.abm_grid_spin.setRange(5, 100)
        self.abm_grid_spin.setValue(20)
        config_layout.addRow("Grid Size:", self.abm_grid_spin)
        
        self.abm_goods_combo = QComboBox()
        self.abm_goods_combo.addItems(["2 Goods", "3 Goods", "4 Goods"])
        config_layout.addRow("Number of Goods:", self.abm_goods_combo)
        
        layout.addWidget(selector_group)
        layout.addWidget(quick_config)
        layout.addStretch()
        
        return tab
    
    def create_abm_protocols_tab(self):
        """
        Protocol selection for ABM
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search protocol
        search_group = QGroupBox("Search Protocol")
        search_layout = QVBoxLayout(search_group)
        self.abm_search_combo = QComboBox()
        self.abm_search_combo.addItems([
            "Legacy (Distance-based)",
            "Random Walk",
            "Myopic (Greedy)",
            "Memory-based"
        ])
        search_layout.addWidget(self.abm_search_combo)
        
        # Matching protocol
        matching_group = QGroupBox("Matching Protocol")
        matching_layout = QVBoxLayout(matching_group)
        self.abm_matching_combo = QComboBox()
        self.abm_matching_combo.addItems([
            "Legacy (Bilateral)",
            "Random Pairing",
            "Greedy Surplus",
            "Stable Matching"
        ])
        matching_layout.addWidget(self.abm_matching_combo)
        
        # Bargaining protocol
        bargaining_group = QGroupBox("Bargaining Protocol")
        bargaining_layout = QVBoxLayout(bargaining_group)
        self.abm_bargaining_combo = QComboBox()
        self.abm_bargaining_combo.addItems([
            "Legacy",
            "Split the Difference",
            "Take it or Leave it",
            "Nash Bargaining"
        ])
        bargaining_layout.addWidget(self.abm_bargaining_combo)
        
        layout.addWidget(search_group)
        layout.addWidget(matching_group)
        layout.addWidget(bargaining_group)
        layout.addStretch()
        
        return tab
```

### Game Theory Page

```python
    def create_gt_page(self):
        """
        Create Game Theory analysis page
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Agent configuration
        agents_group = QGroupBox("Agent Configuration")
        agents_layout = QFormLayout(agents_group)
        
        # Agent A utility
        self.gt_utility_a_combo = QComboBox()
        self.gt_utility_a_combo.addItems([
            "Cobb-Douglas",
            "CES",
            "Leontief",
            "Quadratic"
        ])
        agents_layout.addRow("Agent A Utility:", self.gt_utility_a_combo)
        
        # Agent A endowment
        self.gt_endow_a_good1 = QSpinBox()
        self.gt_endow_a_good1.setRange(0, 200)
        self.gt_endow_a_good1.setValue(100)
        agents_layout.addRow("Agent A Good 1:", self.gt_endow_a_good1)
        
        self.gt_endow_a_good2 = QSpinBox()
        self.gt_endow_a_good2.setRange(0, 200)
        self.gt_endow_a_good2.setValue(0)
        agents_layout.addRow("Agent A Good 2:", self.gt_endow_a_good2)
        
        # Agent B configuration (similar)
        # ...
        
        # Analysis options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.gt_contract_curve_check = QCheckBox("Show Contract Curve")
        self.gt_equilibrium_check = QCheckBox("Compute Equilibrium")
        self.gt_bargaining_check = QCheckBox("Test Bargaining Protocols")
        
        analysis_layout.addWidget(self.gt_contract_curve_check)
        analysis_layout.addWidget(self.gt_equilibrium_check)
        analysis_layout.addWidget(self.gt_bargaining_check)
        
        # Bargaining protocol selection
        self.gt_protocol_combo = QComboBox()
        self.gt_protocol_combo.addItems([
            "Nash Bargaining",
            "Kalai-Smorodinsky",
            "Rubinstein",
            "Equal Split"
        ])
        analysis_layout.addWidget(QLabel("Bargaining Protocol:"))
        analysis_layout.addWidget(self.gt_protocol_combo)
        
        layout.addWidget(agents_group)
        layout.addWidget(analysis_group)
        
        # Launch button
        self.gt_launch_btn = QPushButton("Launch Edgeworth Box")
        self.gt_launch_btn.setMinimumHeight(50)
        self.gt_launch_btn.clicked.connect(self.launch_game_theory)
        layout.addWidget(self.gt_launch_btn)
        
        layout.addStretch()
        
        return page
```

---

## Week 14: Integration and Polish

### Launch Manager

```python
class LaunchManager:
    """
    Manages launching different simulation tracks
    """
    
    def __init__(self):
        self.active_simulations = {}
        self.results_cache = {}
    
    def launch_abm(self, config):
        """
        Launch Agent-Based simulation
        """
        # Create scenario from configuration
        scenario = self.create_abm_scenario(config)
        
        # Initialize simulation
        from vmt_engine.simulation import Simulation
        sim = Simulation(scenario)
        
        # Launch pygame renderer in separate process
        import multiprocessing
        
        def run_abm():
            from vmt_pygame.renderer import PygameRenderer
            renderer = PygameRenderer(sim)
            renderer.run()
        
        process = multiprocessing.Process(target=run_abm)
        process.start()
        
        # Track active simulation
        sim_id = self.generate_sim_id()
        self.active_simulations[sim_id] = {
            'type': 'abm',
            'process': process,
            'config': config,
            'start_time': datetime.now()
        }
        
        return sim_id
    
    def launch_game_theory(self, config):
        """
        Launch Game Theory Edgeworth Box
        """
        # Create agents from configuration
        agent_a = self.create_agent(config['agent_a'])
        agent_b = self.create_agent(config['agent_b'])
        
        # Initialize exchange engine
        from vmt_engine.game_theory import TwoAgentExchange
        engine = TwoAgentExchange(agent_a, agent_b)
        
        # Launch visualizer
        from vmt_engine.game_theory.visualization import EdgeworthBoxVisualizer
        visualizer = EdgeworthBoxVisualizer(engine)
        
        # Configure analysis options
        if config.get('show_contract_curve'):
            engine.compute_contract_curve()
        
        if config.get('compute_equilibrium'):
            engine.compute_competitive_equilibrium()
        
        # Show in separate window
        visualizer.show()
        
        # Track
        sim_id = self.generate_sim_id()
        self.active_simulations[sim_id] = {
            'type': 'game_theory',
            'engine': engine,
            'visualizer': visualizer,
            'config': config,
            'start_time': datetime.now()
        }
        
        return sim_id
    
    def create_abm_scenario(self, config):
        """
        Build scenario dictionary from UI configuration
        """
        return {
            'grid': {
                'width': config['grid_size'],
                'height': config['grid_size']
            },
            'agents': self.generate_agents_config(
                config['num_agents'],
                config['utility_types'],
                config['endowments']
            ),
            'protocols': {
                'search': config['search_protocol'],
                'matching': config['matching_protocol'],
                'bargaining': config['bargaining_protocol']
            },
            'parameters': config.get('parameters', {}),
            'seed': config.get('seed', None)
        }
```

### Comparison Tool

```python
class ComparisonTool(QDialog):
    """
    Compare results across different tracks/configurations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cross-Track Comparison")
        self.setMinimumSize(800, 600)
        self.results = {}
        self.init_ui()
    
    def init_ui(self):
        """
        Build comparison interface
        """
        layout = QVBoxLayout(self)
        
        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Track", "Configuration", "Efficiency", 
            "Convergence", "Trade Volume", "Notes"
        ])
        
        # Chart area
        self.chart_widget = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_widget)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.chart_widget)
        
        layout.addWidget(splitter)
        
        # Controls
        controls = self.create_controls()
        layout.addWidget(controls)
    
    def add_result(self, track_name, config, result):
        """
        Add simulation result for comparison
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Populate row
        self.table.setItem(row, 0, QTableWidgetItem(track_name))
        self.table.setItem(row, 1, QTableWidgetItem(self.config_summary(config)))
        self.table.setItem(row, 2, QTableWidgetItem(f"{result['efficiency']*100:.1f}%"))
        self.table.setItem(row, 3, QTableWidgetItem(str(result['convergence'])))
        self.table.setItem(row, 4, QTableWidgetItem(str(result['trade_volume'])))
        self.table.setItem(row, 5, QTableWidgetItem(result.get('notes', '')))
        
        # Store full result
        self.results[f"{track_name}_{row}"] = result
        
        # Update chart
        self.update_chart()
    
    def update_chart(self):
        """
        Update comparison visualization
        """
        # Clear existing chart
        for i in reversed(range(self.chart_layout.count())):
            self.chart_layout.itemAt(i).widget().setParent(None)
        
        # Create matplotlib figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        
        fig = Figure(figsize=(8, 4))
        canvas = FigureCanvasQTAgg(fig)
        
        # Create subplots
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        
        # Extract data for plotting
        tracks = []
        efficiencies = []
        convergence_times = []
        
        for i in range(self.table.rowCount()):
            tracks.append(self.table.item(i, 0).text())
            eff_text = self.table.item(i, 2).text()
            efficiencies.append(float(eff_text.strip('%')) / 100)
            
            conv_text = self.table.item(i, 3).text()
            try:
                convergence_times.append(int(conv_text))
            except:
                convergence_times.append(0)
        
        # Plot efficiency comparison
        ax1.bar(range(len(tracks)), efficiencies)
        ax1.set_xticks(range(len(tracks)))
        ax1.set_xticklabels(tracks, rotation=45)
        ax1.set_ylabel('Efficiency')
        ax1.set_title('Efficiency Comparison')
        ax1.set_ylim(0, 1)
        
        # Plot convergence times
        ax2.bar(range(len(tracks)), convergence_times)
        ax2.set_xticks(range(len(tracks)))
        ax2.set_xticklabels(tracks, rotation=45)
        ax2.set_ylabel('Convergence Time (ticks)')
        ax2.set_title('Convergence Speed')
        
        fig.tight_layout()
        
        self.chart_layout.addWidget(canvas)
```

### Settings and Preferences

```python
class SettingsDialog(QDialog):
    """
    Application settings and preferences
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VMT Settings")
        self.settings = QSettings("VMT", "UnifiedLauncher")
        self.init_ui()
    
    def init_ui(self):
        """
        Build settings interface
        """
        layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        
        # General settings
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Display settings
        display_tab = self.create_display_tab()
        tabs.addTab(display_tab, "Display")
        
        # Performance settings
        performance_tab = self.create_performance_tab()
        tabs.addTab(performance_tab, "Performance")
        
        # Educational settings
        education_tab = self.create_education_tab()
        tabs.addTab(education_tab, "Educational Mode")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def create_education_tab(self):
        """
        Educational mode settings
        """
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Mode selection
        self.edu_mode_combo = QComboBox()
        self.edu_mode_combo.addItems([
            "Research Mode (Full Features)",
            "Educational Mode (Guided)",
            "Tutorial Mode (Step-by-step)"
        ])
        layout.addRow("Interface Mode:", self.edu_mode_combo)
        
        # Complexity level
        self.complexity_slider = QSlider(Qt.Orientation.Horizontal)
        self.complexity_slider.setRange(1, 5)
        self.complexity_slider.setValue(3)
        layout.addRow("Complexity Level:", self.complexity_slider)
        
        # Hints and guidance
        self.show_hints_check = QCheckBox("Show hints and tooltips")
        self.show_theory_check = QCheckBox("Show theoretical explanations")
        self.progressive_check = QCheckBox("Progressive complexity")
        
        layout.addRow(self.show_hints_check)
        layout.addRow(self.show_theory_check)
        layout.addRow(self.progressive_check)
        
        return tab
```

### Menu System

```python
    def create_menu_bar(self):
        """
        Create application menu bar
        """
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = file_menu.addAction("New Simulation")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_simulation)
        
        open_action = file_menu.addAction("Open Scenario...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_scenario)
        
        save_action = file_menu.addAction("Save Configuration...")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_configuration)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        comparison_action = view_menu.addAction("Comparison Tool")
        comparison_action.triggered.connect(self.show_comparison)
        
        results_action = view_menu.addAction("Results Viewer")
        results_action.triggered.connect(self.show_results)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        batch_action = tools_menu.addAction("Batch Runner")
        batch_action.triggered.connect(self.show_batch_runner)
        
        analyzer_action = tools_menu.addAction("Data Analyzer")
        analyzer_action.triggered.connect(self.show_analyzer)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        tutorial_action = help_menu.addAction("Interactive Tutorial")
        tutorial_action.triggered.connect(self.show_tutorial)
        
        docs_action = help_menu.addAction("Documentation")
        docs_action.triggered.connect(self.show_documentation)
        
        about_action = help_menu.addAction("About VMT")
        about_action.triggered.connect(self.show_about)
```

---

## Integration Points

### Scenario Management

```python
class ScenarioManager:
    """
    Manage scenarios across all tracks
    """
    
    def __init__(self):
        self.scenarios_dir = Path("scenarios")
        self.user_scenarios_dir = Path.home() / ".vmt" / "scenarios"
        self.cached_scenarios = {}
    
    def get_available_scenarios(self, track=None):
        """
        Get list of available scenarios for track
        """
        scenarios = []
        
        # Built-in scenarios
        for path in self.scenarios_dir.rglob("*.yaml"):
            scenario = self.load_scenario(path)
            if track is None or scenario.get('track') == track:
                scenarios.append(scenario)
        
        # User scenarios
        if self.user_scenarios_dir.exists():
            for path in self.user_scenarios_dir.rglob("*.yaml"):
                scenario = self.load_scenario(path)
                if track is None or scenario.get('track') == track:
                    scenarios.append(scenario)
        
        return scenarios
    
    def create_scenario_from_ui(self, ui_config):
        """
        Convert UI configuration to scenario format
        """
        track = ui_config['track']
        
        if track == 'abm':
            return self.create_abm_scenario(ui_config)
        elif track == 'game_theory':
            return self.create_gt_scenario(ui_config)
        elif track == 'neoclassical':
            return self.create_neo_scenario(ui_config)
```

### Cross-Track Protocol Registry

```python
class UnifiedProtocolRegistry:
    """
    Manage protocols across all tracks
    """
    
    def __init__(self):
        self.protocols = {
            'bargaining': {},
            'matching': {},
            'search': {}
        }
        self.load_all_protocols()
    
    def load_all_protocols(self):
        """
        Load protocols from all modules
        """
        # Game Theory protocols
        from vmt_engine.game_theory.bargaining import (
            NashBargaining, KalaiSmorodinsky, RubinsteinBargaining
        )
        
        self.register('bargaining', 'nash', NashBargaining)
        self.register('bargaining', 'kalai_smorodinsky', KalaiSmorodinsky)
        self.register('bargaining', 'rubinstein', RubinsteinBargaining)
        
        # Agent-Based search protocols
        from vmt_engine.agent_based.search import (
            RandomWalk, MyopicSearch, MemoryBasedSearch
        )
        
        self.register('search', 'random_walk', RandomWalk)
        
    def get_protocols_for_track(self, track):
        """
        Get available protocols for specific track
        """
        if track == 'abm':
            return {
                'search': list(self.protocols['search'].keys()),
                'matching': list(self.protocols['matching'].keys()),
                'bargaining': list(self.protocols['bargaining'].keys())
            }
        elif track == 'game_theory':
            return {
                'bargaining': list(self.protocols['bargaining'].keys())
            }
        else:
            return {}
```

---

## Deliverables

1. **Unified launcher application** with track selection
2. **Configuration interfaces** for each track
3. **Comparison tool** for cross-track analysis
4. **Settings system** with educational/research modes
5. **Integrated help system** with tutorials
6. **Batch running capability** for research

---

## Success Metrics

- ✅ Seamless navigation between tracks
- ✅ Consistent user experience across paradigms
- ✅ Easy scenario configuration for all tracks
- ✅ Results comparison across different approaches
- ✅ Educational mode with progressive complexity
