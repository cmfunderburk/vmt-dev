"""
Pygame visualization for VMT simulation.

DEPRECATION NOTICE: Money visualization features (money labels, lambda heatmap,
sparkles, exchange regime display) are DEPRECATED after money system removal.
They are retained but non-functional. Future UI redesign will remove this code.
"""

import math
import os
import platform
import pygame
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from vmt_engine.simulation import Simulation
    from vmt_engine.core import Agent


class VMTRenderer:
    """Renders VMT simulation using Pygame."""
    
    def __init__(self, simulation: 'Simulation', cell_size: Optional[int] = None):
        """
        Initialize renderer with automatic display scaling.
        
        Args:
            simulation: The simulation to render
            cell_size: Size of each grid cell in pixels (None = auto-detect)
        """
        pygame.init()
        
        self.sim = simulation
        
        # Panel toggle states
        self.show_left_panel = True
        self.show_hud_panel = True
        
        # Fixed default window size for good tiling behavior
        DEFAULT_WIDTH = 1200
        DEFAULT_HEIGHT = 900
        
        # Initialize camera offset for scrolling
        self.camera_x = 0
        self.camera_y = 0
        
        # Create resizable window
        self.screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
        scenario_name = simulation.config.name
        seed = simulation.seed
        pygame.display.set_caption(f"VMT v1 - {scenario_name} (seed: {seed})")
        
        self.use_dark_theme = self._should_use_dark_theme()
        self._init_colors()

        # Accent colors (theme-independent)
        self.COLOR_RED = (255, 100, 100)
        self.COLOR_BLUE = (100, 100, 255)
        self.COLOR_GREEN = (100, 255, 100)
        self.COLOR_PURPLE = (200, 100, 255)
        self.COLOR_YELLOW = (255, 255, 100)
        self.COLOR_ARROW_TRADE = (100, 255, 100)      # Green for trade targeting
        self.COLOR_ARROW_FORAGE = (255, 165, 0)       # Orange for forage targeting
        self.COLOR_ARROW_IDLE_HOME = (173, 216, 230)  # Light blue for idle home targeting
        self.COLOR_IDLE_BORDER = (255, 100, 100)      # Red border for idle agents
        self.COLOR_GOLD = (255, 215, 0)
        self.COLOR_DARK_GOLD = (218, 165, 32)
        
        # Calculate initial layout
        self._calculate_layout(DEFAULT_WIDTH, DEFAULT_HEIGHT, cell_size)
        
        # Track trade events for visualization
        self.recent_trades = self.sim.telemetry.recent_trades_for_renderer
        
        # Arrow visualization state
        self.show_trade_arrows = False
        self.show_forage_arrows = False
        
        # Mode overlay
        self.show_mode_regime_overlay = True  # Toggle with 'I' - shows mode only
        
        # Exchange rate tracking
        self.trade_history = []  # List of (tick, exchange_pair_type, rate) tuples
    
    def _should_use_dark_theme(self) -> bool:
        """Determine whether to enable the renderer's dark theme."""
        # Explicit light theme override always wins.
        if os.getenv("VMT_FORCE_LIGHT_THEME") is not None:
            return False

        # Allow explicit dark override via env var (treat 0/false/no as disabled).
        force_dark = os.getenv("VMT_FORCE_DARK_THEME")
        if force_dark is not None:
            return force_dark.strip().lower() not in {"0", "false", "no", ""}

        # Default to dark theme on Linux where SDL falls back to light widgets.
        return platform.system().lower() == "linux"

    def _init_colors(self) -> None:
        """Initialize renderer colors based on the active theme."""
        if self.use_dark_theme:
            self.COLOR_BACKGROUND = (16, 16, 22)
            self.COLOR_PANEL_BACKGROUND = (30, 32, 38)
            self.COLOR_PANEL_BORDER = (90, 90, 100)
            self.COLOR_GRID_LINE = (60, 60, 72)
            self.COLOR_TEXT = (235, 235, 240)
            self.COLOR_TEXT_MUTED = (180, 180, 190)
            self.COLOR_OUTLINE = (210, 210, 215)
            self.COLOR_TEXT_OUTLINE = (0, 0, 0)
        else:
            self.COLOR_BACKGROUND = (255, 255, 255)
            self.COLOR_PANEL_BACKGROUND = (240, 240, 240)
            self.COLOR_PANEL_BORDER = (0, 0, 0)
            self.COLOR_GRID_LINE = (200, 200, 200)
            self.COLOR_TEXT = (0, 0, 0)
            self.COLOR_TEXT_MUTED = (80, 80, 80)
            self.COLOR_OUTLINE = (0, 0, 0)
            self.COLOR_TEXT_OUTLINE = (0, 0, 0)

        # Legacy names retained for downstream code until fully migrated.
        self.COLOR_WHITE = self.COLOR_BACKGROUND
        self.COLOR_LIGHT_GRAY = self.COLOR_PANEL_BACKGROUND
        self.COLOR_GRAY = self.COLOR_GRID_LINE
        self.COLOR_BLACK = self.COLOR_TEXT

    def _calculate_layout(self, window_width: int, window_height: int, forced_cell_size: Optional[int] = None):
        """
        Calculate layout parameters based on window dimensions.
        
        Args:
            window_width: Current window width in pixels
            window_height: Current window height in pixels
            forced_cell_size: Override cell size (None = auto-calculate)
        """
        grid_size = self.sim.grid.N
        
        # Base panel dimensions (will scale based on window size)
        base_left_panel_width = 250
        base_hud_height = 100
        
        # Scale panels proportionally to window size
        # Left panel: 15-25% of width, clamped to 200-400px
        left_panel_ratio = 0.20
        self.left_panel_width = int(max(200, min(400, window_width * left_panel_ratio)))
        
        # HUD height: 8-12% of height, clamped to 80-120px
        hud_ratio = 0.10
        self.hud_height = int(max(80, min(120, window_height * hud_ratio)))
        
        # Calculate available space for grid (accounting for panels if shown)
        available_width = window_width - (self.left_panel_width if self.show_left_panel else 0)
        available_height = window_height - (self.hud_height if self.show_hud_panel else 0)
        
        # Calculate optimal cell size if not forced
        if forced_cell_size is None:
            optimal_cell_size = min(
                available_width // grid_size,
                available_height // grid_size
            )
            # Allow cells to shrink to 5px minimum
            self.cell_size = max(5, optimal_cell_size)
        else:
            self.cell_size = forced_cell_size
        
        # Calculate actual grid dimensions
        grid_pixel_size = grid_size * self.cell_size
        
        # Determine if scrolling is needed
        self.needs_scrolling = (
            grid_pixel_size > available_width or 
            grid_pixel_size > available_height
        )
        
        # Set grid viewport dimensions
        if self.needs_scrolling:
            self.width = min(grid_pixel_size, available_width)
            self.height = min(grid_pixel_size, available_height)
        else:
            self.width = grid_pixel_size
            self.height = grid_pixel_size
        
        # Total window dimensions including panels
        self.total_window_width = self.width + (self.left_panel_width if self.show_left_panel else 0)
        self.window_height = self.height + (self.hud_height if self.show_hud_panel else 0)
        
        # Constrain camera position to valid bounds after resize
        if self.needs_scrolling:
            max_x = max(0, grid_pixel_size - self.width)
            max_y = max(0, grid_pixel_size - self.height)
            self.camera_x = min(self.camera_x, max_x)
            self.camera_y = min(self.camera_y, max_y)
        else:
            self.camera_x = 0
            self.camera_y = 0
        
        # Progressive UI element hiding for very small cell sizes
        self.show_inventory_labels = self.cell_size >= 15
        self.show_agent_labels = self.cell_size >= 8
        self.show_resource_labels = self.cell_size >= 10
        self.show_home_indicators = self.cell_size >= 6
        
        # Scale fonts proportionally to cell size
        base_font_size = max(8, min(16, self.cell_size // 3))
        small_font_size = max(7, min(12, self.cell_size // 4))
        self.font = pygame.font.SysFont('arial', base_font_size)
        self.small_font = pygame.font.SysFont('arial', small_font_size)
    
    def handle_resize(self, new_width: int, new_height: int):
        """
        Handle window resize events.
        
        Args:
            new_width: New window width
            new_height: New window height
        """
        # Enforce minimum window size
        MIN_WIDTH = 640
        MIN_HEIGHT = 480
        
        new_width = max(MIN_WIDTH, new_width)
        new_height = max(MIN_HEIGHT, new_height)
        
        # NOTE: Do NOT call pygame.display.set_mode() here!
        # The display surface is automatically resized by pygame when VIDEORESIZE occurs.
        # Calling set_mode() again would trigger another VIDEORESIZE event (infinite loop).
        # Just recalculate the layout with the new dimensions.
        
        # Recalculate layout
        self._calculate_layout(new_width, new_height)
    
    def handle_camera_input(self, keys):
        """Handle camera movement with arrow keys."""
        if not self.needs_scrolling:
            return
        
        SCROLL_SPEED = self.cell_size  # Scroll by one cell at a time
        grid_pixel_size = self.sim.grid.N * self.cell_size
        
        if keys[pygame.K_LEFT]:
            self.camera_x = max(0, self.camera_x - SCROLL_SPEED)
        if keys[pygame.K_RIGHT]:
            max_x = max(0, grid_pixel_size - self.width)
            self.camera_x = min(max_x, self.camera_x + SCROLL_SPEED)
        if keys[pygame.K_UP]:
            self.camera_y = max(0, self.camera_y - SCROLL_SPEED)
        if keys[pygame.K_DOWN]:
            max_y = max(0, grid_pixel_size - self.height)
            self.camera_y = min(max_y, self.camera_y + SCROLL_SPEED)
    
    def to_screen_coords(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates with camera offset and left panel."""
        left_offset = self.left_panel_width if self.show_left_panel else 0
        return (
            left_offset + grid_x * self.cell_size - self.camera_x,
            grid_y * self.cell_size - self.camera_y
        )
    
    def is_visible(self, screen_x, screen_y):
        """Check if coordinates are visible in current viewport (accounting for left panel)."""
        left_offset = self.left_panel_width if self.show_left_panel else 0
        return (
            left_offset - self.cell_size <= screen_x <= self.total_window_width + self.cell_size and
            -self.cell_size <= screen_y <= self.height + self.cell_size
        )
    
    def render(self):
        """Render the current simulation state."""
        self.screen.fill(self.COLOR_BACKGROUND)
        
        # Draw left info panel if enabled
        if self.show_left_panel:
            self.draw_left_panel()
        
        self.draw_grid()
        self.draw_resources()
        
        # Highlight high-activity cells (5+ agents)
        self.draw_high_activity_cells()
        
        # Draw home positions if cell size is large enough
        if self.show_home_indicators:
            self.draw_home_positions()
        
        # Draw agents
        self.draw_agents()
        
        self.draw_target_arrows()
        self.draw_trade_indicators()
        
        # Draw HUD if enabled
        if self.show_hud_panel:
            self.draw_hud()
        
        pygame.display.flip()
    
    def draw_grid(self):
        """Draw grid lines with camera offset and viewport culling."""
        # Only draw visible grid lines
        start_x = self.camera_x // self.cell_size
        end_x = min(self.sim.grid.N, (self.camera_x + self.width) // self.cell_size + 1)
        start_y = self.camera_y // self.cell_size
        end_y = min(self.sim.grid.N, (self.camera_y + self.height) // self.cell_size + 1)
        
        left_offset = self.left_panel_width if self.show_left_panel else 0
        
        for x in range(start_x, end_x + 1):
            screen_x = left_offset + x * self.cell_size - self.camera_x
            pygame.draw.line(
                self.screen, self.COLOR_GRID_LINE,
                (screen_x, 0), (screen_x, self.height),
                1
            )
        
        for y in range(start_y, end_y + 1):
            screen_y = y * self.cell_size - self.camera_y
            pygame.draw.line(
                self.screen, self.COLOR_GRID_LINE,
                (left_offset, screen_y), (left_offset + self.width, screen_y),
                1
            )
    
    def draw_resources(self):
        """Draw resource cells with camera offset and viewport culling."""
        for cell in self.sim.grid.cells.values():
            if cell.resource.amount > 0 and cell.resource.type:
                x, y = cell.position
                screen_x, screen_y = self.to_screen_coords(x, y)
                
                # Skip if not visible
                if not self.is_visible(screen_x, screen_y):
                    continue
                
                # Color based on resource type
                if cell.resource.type == "A":
                    color = self.COLOR_RED
                else:  # "B"
                    color = self.COLOR_BLUE
                
                # Alpha based on amount (lighter for less)
                alpha = min(255, 100 + cell.resource.amount * 30)
                surface = pygame.Surface((self.cell_size, self.cell_size))
                surface.set_alpha(alpha)
                surface.fill(color)
                self.screen.blit(surface, (screen_x, screen_y))
                
                # Draw amount label if cell size permits
                if self.show_resource_labels:
                    label = self.small_font.render(
                        f"{cell.resource.type}:{cell.resource.amount}",
                        True, self.COLOR_TEXT
                    )
                    self.screen.blit(label, (screen_x + 2, screen_y + 2))
    
    def draw_high_activity_cells(self):
        """Draw yellow outline for cells with 5 or more agents to highlight high-activity zones."""
        # Group agents by position
        position_groups = self.group_agents_by_position()
        
        # Draw yellow outline for cells with 5+ agents
        for pos, agents in position_groups.items():
            if len(agents) >= 5:
                x, y = pos
                screen_x, screen_y = self.to_screen_coords(x, y)
                
                # Skip if not visible
                if not self.is_visible(screen_x, screen_y):
                    continue
                
                # Draw thick yellow outline
                pygame.draw.rect(
                    self.screen, 
                    self.COLOR_YELLOW,
                    (screen_x, screen_y, self.cell_size, self.cell_size),
                    3  # Line width of 3 pixels for visibility
                )
    
    def draw_home_positions(self):
        """Draw home position indicators for all agents."""
        for agent in self.sim.agents:
            if agent.home_pos is None:
                continue
                
            x, y = agent.home_pos
            screen_x, screen_y = self.to_screen_coords(x, y)
            
            # Skip if not visible
            if not self.is_visible(screen_x, screen_y):
                continue
            
            # Draw a small square in the corner of the home cell
            home_size = max(3, self.cell_size // 8)
            home_x = screen_x + self.cell_size - home_size - 2
            home_y = screen_y + 2
            
            # Draw home indicator as a small square
            pygame.draw.rect(
                self.screen, self.COLOR_OUTLINE, 
                (home_x, home_y, home_size, home_size)
            )
            pygame.draw.rect(
                self.screen, self.COLOR_TEXT, 
                (home_x + 1, home_y + 1, home_size - 2, home_size - 2)
            )
    
    def group_agents_by_position(self) -> dict[tuple[int, int], list['Agent']]:
        """
        Group agents by their grid position for smart co-location rendering.
        
        Returns:
            Dictionary mapping (x, y) position to list of agents at that position,
            sorted by agent ID for deterministic rendering.
        """
        position_groups = {}
        
        for agent in self.sim.agents:
            pos = agent.pos
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(agent)
        
        # Sort agents within each group by ID for deterministic rendering
        for pos in position_groups:
            position_groups[pos].sort(key=lambda a: a.id)
        
        return position_groups
    
    def calculate_agent_radius(self, cell_size: int, agent_count: int) -> int:
        """
        Calculate optimal agent radius based on co-location count.
        
        Strategy:
        - 1 agent: cell_size // 3 (current behavior)
        - 2 agents: cell_size // 4 (75% scale)
        - 3 agents: cell_size // 5 (60% scale)
        - 4+ agents: cell_size // (count + 2) with floor of 2px
        
        Args:
            cell_size: Size of grid cell in pixels
            agent_count: Number of co-located agents
            
        Returns:
            Radius in pixels (minimum 2px for visibility)
        """
        if agent_count == 1:
            return max(2, cell_size // 3)
        elif agent_count == 2:
            return max(2, cell_size // 4)
        elif agent_count == 3:
            return max(2, cell_size // 5)
        else:
            return max(2, cell_size // (agent_count + 2))
    
    def calculate_agent_display_position(
        self,
        agent_index: int,
        total_agents: int,
        cell_center_x: int,
        cell_center_y: int
    ) -> tuple[int, int]:
        """
        Calculate display position for agent within a co-located group.
        
        Uses geometric layouts to minimize overlap:
        - 1 agent: center (current behavior)
        - 2 agents: diagonal opposite corners
        - 3 agents: triangle pattern (one top, two bottom)
        - 4 agents: one per corner
        - 5+ agents: circle pack around center
        
        Args:
            agent_index: Index of agent in sorted group (0 to total_agents-1)
            total_agents: Total number of agents at this position
            cell_center_x: Center x coordinate of cell in screen pixels
            cell_center_y: Center y coordinate of cell in screen pixels
            
        Returns:
            (px, py) display coordinates for this agent
        """
        if total_agents == 1:
            # Single agent - use center (current behavior)
            return (cell_center_x, cell_center_y)
        
        elif total_agents == 2:
            # Two agents - opposite corners (diagonal)
            # Agent 0: upper-left, Agent 1: lower-right
            offset = self.cell_size // 4
            if agent_index == 0:
                return (cell_center_x - offset, cell_center_y - offset)
            else:
                return (cell_center_x + offset, cell_center_y + offset)
        
        elif total_agents == 3:
            # Three agents - triangle pattern
            # Angles: 90° (top), 210° (bottom-left), 330° (bottom-right)
            offset = self.cell_size // 4
            angles = [90, 210, 330]
            angle_rad = math.radians(angles[agent_index])
            px = cell_center_x + int(offset * math.cos(angle_rad))
            py = cell_center_y - int(offset * math.sin(angle_rad))  # Negative because y increases downward
            return (px, py)
        
        elif total_agents == 4:
            # Four agents - one per corner
            offset = self.cell_size // 4
            corners = [
                (-offset, -offset),  # Upper-left
                (offset, -offset),   # Upper-right
                (-offset, offset),   # Lower-left
                (offset, offset),    # Lower-right
            ]
            dx, dy = corners[agent_index]
            return (cell_center_x + dx, cell_center_y + dy)
        
        else:
            # 5+ agents - circle pack around center
            offset = self.cell_size // 3
            angle_step = 360 / total_agents
            angle_rad = math.radians(agent_index * angle_step)
            px = cell_center_x + int(offset * math.cos(angle_rad))
            py = cell_center_y - int(offset * math.sin(angle_rad))
            return (px, py)
    
    def get_agent_color(self, agent: 'Agent') -> tuple[int, int, int]:
        """
        Get display color for agent based on utility type.
        
        Args:
            agent: The agent to get color for
            
        Returns:
            RGB color tuple
        """
        if agent.utility:
            utility_type = agent.utility.__class__.__name__
            if utility_type == "UCES":
                return self.COLOR_GREEN
            elif utility_type == "ULinear":
                return self.COLOR_PURPLE
            elif utility_type == "UQuadratic":
                return self.COLOR_BLUE
            elif utility_type == "UTranslog":
                return (255, 140, 0)  # Dark orange
            elif utility_type == "UStoneGeary":
                return (255, 20, 147)  # Deep pink
            else:
                return self.COLOR_YELLOW
        return self.COLOR_TEXT
    
    def get_utility_type_label(self, agent: 'Agent') -> str:
        """
        Get 2-3 letter label for agent's utility type.
        
        Args:
            agent: The agent to get label for
            
        Returns:
            Short string label (e.g., "CES", "LIN", "QUA", "TRL", "SG")
        """
        if agent.utility:
            utility_type = agent.utility.__class__.__name__
            if utility_type == "UCES":
                return "CES"
            elif utility_type == "ULinear":
                return "LIN"
            elif utility_type == "UQuadratic":
                return "QUA"
            elif utility_type == "UTranslog":
                return "TRL"
            elif utility_type == "UStoneGeary":
                return "SG"
            else:
                return "???"
        return "???"
    
    def draw_group_inventory_labels(
        self,
        agents: list['Agent'],
        screen_x: int,
        screen_y: int,
        agent_count: int
    ):
        """
        Draw inventory labels for a group of co-located agents.
        
        Strategy:
        - 1 agent: Label below agent (current behavior)
        - 2-3 agents: Stack labels vertically below cell
        - 4+ agents: Show "N agents" summary instead of individual inventories
        
        Args:
            agents: List of co-located agents (sorted by ID)
            screen_x: Screen x coordinate of cell top-left
            screen_y: Screen y coordinate of cell top-left
            agent_count: Number of agents in group
        """
        # Money system removed - always barter-only
        has_money = False
        
        cell_center_x = screen_x + self.cell_size // 2
        cell_bottom_y = screen_y + self.cell_size
        
        if agent_count == 1:
            # Single agent - draw inventory below (current behavior)
            agent = agents[0]
            inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B}"
            
            inv_label = self.small_font.render(inv_text, True, self.COLOR_TEXT)
            inv_width = inv_label.get_width()
            self.screen.blit(inv_label, (cell_center_x - inv_width // 2, cell_bottom_y + 2))
        
        elif agent_count <= 3:
            # 2-3 agents - stack labels vertically
            for idx, agent in enumerate(agents):
                inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B}"
                
                inv_label = self.small_font.render(inv_text, True, self.COLOR_TEXT)
                inv_width = inv_label.get_width()
                y_offset = cell_bottom_y + 2 + (idx * 12)  # 12px spacing between labels
                
                # Check if label would go off screen
                if y_offset + 12 <= self.height:
                    self.screen.blit(inv_label, (cell_center_x - inv_width // 2, y_offset))
        
        else:
            # 4+ agents - show summary only
            summary_text = f"{agent_count} agents at ({agents[0].pos[0]}, {agents[0].pos[1]})"
            summary_label = self.small_font.render(summary_text, True, self.COLOR_TEXT)
            summary_width = summary_label.get_width()
            self.screen.blit(summary_label, (cell_center_x - summary_width // 2, cell_bottom_y + 2))
    
    def draw_agents(self):
        """
        Draw agents with smart co-location handling.
        
        When multiple agents occupy the same cell, they are rendered with:
        - Scaled-down size (proportional to agent count)
        - Non-overlapping geometric layouts (diagonal, triangle, corners, circle pack)
        - Organized inventory labels
        
        This is a pure visualization enhancement - simulation positions remain unchanged.
        """
        # Group agents by position
        position_groups = self.group_agents_by_position()
        
        for pos, agents in position_groups.items():
            x, y = pos
            screen_x, screen_y = self.to_screen_coords(x, y)
            
            # Skip if not visible
            if not self.is_visible(screen_x, screen_y):
                continue
            
            # Calculate cell center
            cell_center_x = screen_x + self.cell_size // 2
            cell_center_y = screen_y + self.cell_size // 2
            
            # Calculate optimal radius for this group size
            agent_count = len(agents)
            radius = self.calculate_agent_radius(self.cell_size, agent_count)
            
            # Draw each agent in the group
            for idx, agent in enumerate(agents):
                # Get display position for this agent
                px, py = self.calculate_agent_display_position(
                    idx, agent_count, cell_center_x, cell_center_y
                )
                
                # Get agent color
                color = self.get_agent_color(agent)
                
                # Draw agent circle
                pygame.draw.circle(self.screen, color, (px, py), radius)
                pygame.draw.circle(
                    self.screen, self.COLOR_OUTLINE, (px, py), radius,
                    max(1, radius // 5)
                )
                
                # Draw agent ID and utility type label (if space permits and labels enabled)
                if self.show_agent_labels and radius >= 5:
                    # Draw agent ID on first line
                    id_label = self.small_font.render(str(agent.id), True, self.COLOR_TEXT)
                    id_height = id_label.get_height()
                    
                    # Get utility type label
                    util_type = self.get_utility_type_label(agent)
                    util_label = self.small_font.render(util_type, True, self.COLOR_TEXT)
                    util_height = util_label.get_height()
                    
                    # Calculate total height and starting y position to center both lines
                    total_height = id_height + util_height
                    start_y = py - total_height // 2
                    
                    # Draw ID label
                    id_rect = id_label.get_rect(center=(px, start_y + id_height // 2))
                    self.screen.blit(id_label, id_rect)
                    
                    # Draw utility type label below ID
                    util_rect = util_label.get_rect(center=(px, start_y + id_height + util_height // 2))
                    self.screen.blit(util_label, util_rect)
            
            # Draw inventory labels below the entire group
            # Disabled to reduce visual clutter - inventory inspection feature coming soon
            # if self.cell_size >= 20:
            #     self.draw_group_inventory_labels(
            #         agents, screen_x, screen_y, agent_count
            #     )
    
    def draw_arrow(self, start_pos, end_pos, color, width=2):
        """
        Draw arrow from start to end position with arrowhead.
        
        Args:
            start_pos: (screen_x, screen_y) tuple
            end_pos: (screen_x, screen_y) tuple  
            color: RGB color tuple
            width: Line width in pixels
        """
        # Draw line
        pygame.draw.line(self.screen, color, start_pos, end_pos, width)
        
        # Calculate arrowhead
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:
            return  # Too short to draw arrowhead
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Arrowhead parameters
        arrow_len = 8
        arrow_angle = math.pi / 6  # 30 degrees
        
        # Calculate arrowhead points
        p1 = (
            end_pos[0] - arrow_len * (dx * math.cos(arrow_angle) + dy * math.sin(arrow_angle)),
            end_pos[1] - arrow_len * (dy * math.cos(arrow_angle) - dx * math.sin(arrow_angle))
        )
        p2 = (
            end_pos[0] - arrow_len * (dx * math.cos(arrow_angle) - dy * math.sin(arrow_angle)),
            end_pos[1] - arrow_len * (dy * math.cos(arrow_angle) + dx * math.sin(arrow_angle))
        )
        
        # Draw arrowhead
        pygame.draw.polygon(self.screen, color, [end_pos, p1, p2])
    
    def draw_target_arrows(self):
        """Draw arrows showing agent movement targets and highlight idle agents."""
        # Track idle agents for border rendering (shown regardless of arrow settings)
        idle_agents = []
        
        arrows_enabled = self.show_trade_arrows or self.show_forage_arrows
        
        for agent in self.sim.agents:
            # Check if agent is idle (no target OR at home and targeting home)
            is_idle = (agent.target_pos is None or 
                      (agent.home_pos is not None and 
                       agent.pos == agent.home_pos and 
                       agent.target_pos == agent.home_pos and 
                       agent.target_agent_id is None))
            
            if is_idle:
                # Idle agent - track for border rendering
                idle_agents.append(agent)
                continue
            
            # Skip arrow rendering if all arrows disabled
            if not arrows_enabled:
                continue
            
            # Determine arrow type
            is_trade = agent.target_agent_id is not None
            is_forage = agent.target_agent_id is None
            is_idle_home = (is_forage and agent.home_pos is not None and 
                          agent.target_pos == agent.home_pos)
            
            # Skip if this arrow type is disabled
            if is_trade and not self.show_trade_arrows:
                continue
            if is_forage and not self.show_forage_arrows:
                continue
            
            # Skip if no target position (should not happen given earlier check)
            if agent.target_pos is None:
                continue
            
            # Convert positions to screen coordinates
            agent_x, agent_y = agent.pos
            target_x, target_y = agent.target_pos
            
            agent_screen = self.to_screen_coords(agent_x, agent_y)
            target_screen = self.to_screen_coords(target_x, target_y)
            
            # Check if either endpoint is visible (viewport culling)
            if not (self.is_visible(agent_screen[0], agent_screen[1]) or 
                    self.is_visible(target_screen[0], target_screen[1])):
                continue
            
            # Calculate cell centers for arrow endpoints
            agent_center = (
                agent_screen[0] + self.cell_size // 2,
                agent_screen[1] + self.cell_size // 2
            )
            target_center = (
                target_screen[0] + self.cell_size // 2,
                target_screen[1] + self.cell_size // 2
            )
            
            # Choose color based on target type
            if is_trade:
                color = self.COLOR_ARROW_TRADE
            elif is_idle_home:
                color = self.COLOR_ARROW_IDLE_HOME
            else:
                color = self.COLOR_ARROW_FORAGE
            
            # Draw arrow
            self.draw_arrow(agent_center, target_center, color, width=2)
        
        # Draw red borders for idle agents
        self.draw_idle_agent_borders(idle_agents)
    
    def draw_idle_agent_borders(self, idle_agents):
        """
        Draw red borders around idle agents (those with no target).
        
        Args:
            idle_agents: List of agents with no target_pos
        """
        # Group idle agents by position for proper rendering
        position_groups = {}
        for agent in idle_agents:
            pos = agent.pos
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(agent)
        
        # Sort agents within each group by ID for deterministic rendering
        for pos in position_groups:
            position_groups[pos].sort(key=lambda a: a.id)
        
        for pos, agents in position_groups.items():
            x, y = pos
            screen_x, screen_y = self.to_screen_coords(x, y)
            
            # Skip if not visible
            if not self.is_visible(screen_x, screen_y):
                continue
            
            # Calculate cell center
            cell_center_x = screen_x + self.cell_size // 2
            cell_center_y = screen_y + self.cell_size // 2
            
            # Calculate optimal radius for this group size
            agent_count = len(agents)
            radius = self.calculate_agent_radius(self.cell_size, agent_count)
            
            # Draw red border for each idle agent
            border_width = max(2, radius // 3)  # Border scales with agent size
            
            for idx, agent in enumerate(agents):
                # Get display position for this agent (same logic as draw_agents)
                px, py = self.calculate_agent_display_position(
                    idx, agent_count, cell_center_x, cell_center_y
                )
                
                # Draw red border circle
                pygame.draw.circle(
                    self.screen, self.COLOR_IDLE_BORDER, (px, py), 
                    radius + border_width, border_width
                )
    
    def draw_agents_with_lambda_heatmap(self):
        """
        Draw agents colored by their lambda_money value (heatmap) - REMOVED.
        Money system removed - falls back to regular agent rendering.
        """
        # Lambda_money removed - fall back to regular rendering
        self.draw_agents()
    
    def draw_trade_indicators(self):
        """Draw indicators for recent trades."""
        # This method is now obsolete as trades are drawn on the HUD
        pass
    
    def draw_hud(self):
        """Draw heads-up display with simulation info."""
        hud_y = self.height + 10
        
        # Background for HUD (spans entire window width including left panel)
        pygame.draw.rect(
            self.screen, self.COLOR_PANEL_BACKGROUND,
            (0, self.height, self.total_window_width, self.hud_height)
        )
        
        # Tick counter
        tick_text = f"Tick: {self.sim.tick}"
        tick_label = self.font.render(tick_text, True, self.COLOR_TEXT)
        self.screen.blit(tick_label, (10, hud_y))
        
        # Agent count
        agent_text = f"Agents: {len(self.sim.agents)}"
        agent_label = self.font.render(agent_text, True, self.COLOR_TEXT)
        self.screen.blit(agent_label, (10, hud_y + 20))
        
        # Mode and trade execution info
        mode = self.sim.current_mode  # "forage", "trade", or "both"
        trade_execution_mode = self.sim.params.get('trade_execution_mode', 'minimum')
        
        mode_text = f"Mode: {mode} | Economy: Barter-Only | Trade Execution: {trade_execution_mode}"
        mode_label = self.font.render(mode_text, True, self.COLOR_TEXT)
        self.screen.blit(mode_label, (10, hud_y + 40))
        
        # Total inventory across all agents
        total_A = sum(a.inventory.A for a in self.sim.agents)
        total_B = sum(a.inventory.B for a in self.sim.agents)
        
        # Money system removed - show only goods inventory
        inv_text = f"Total Inventory - A: {total_A}  B: {total_B}"
        
        inv_label = self.font.render(inv_text, True, self.COLOR_TEXT)
        self.screen.blit(inv_label, (10, hud_y + 60))
        
        # Controls (with scrolling if needed)
        if self.needs_scrolling:
            controls_text = "SPACE=Pause R=Reset S=Step ←→↑↓=Scroll/Speed T/F/A/O=Arrows [=Panel ]=HUD I=Info Q=Quit"
        else:
            controls_text = "SPACE=Pause R=Reset S=Step ↑↓=Speed T/F/A/O=Arrows [=Panel ]=HUD I=Info Q=Quit"
        controls_label = self.small_font.render(controls_text, True, self.COLOR_TEXT)
        self.screen.blit(controls_label, (10, hud_y + 80))
        
        # Arrow toggle status
        arrow_status_parts = []
        if self.show_trade_arrows:
            arrow_status_parts.append("Trade")
        if self.show_forage_arrows:
            arrow_status_parts.append("Forage")
        
        if arrow_status_parts:
            arrow_status = "Arrows: " + "+".join(arrow_status_parts)
        else:
            arrow_status = "Arrows: OFF"
        
        arrow_label = self.small_font.render(arrow_status, True, self.COLOR_TEXT)
        self.screen.blit(arrow_label, (10, hud_y + 95))
        
        # Mode overlay status
        overlay_status = "Mode Overlay: ON" if self.show_mode_regime_overlay else "Mode Overlay: OFF"
        overlay_label = self.small_font.render(overlay_status, True, self.COLOR_TEXT)
        self.screen.blit(overlay_label, (200, hud_y + 95))

        # Recent trades (right-justified, accounting for total window width)
        trade_hud_y = hud_y
        trade_title = self.font.render("Recent Trades:", True, self.COLOR_TEXT)
        trade_title_width = trade_title.get_width()
        trade_x_start = self.total_window_width - trade_title_width - 10  # 10px margin from right edge
        self.screen.blit(trade_title, (trade_x_start, trade_hud_y))
        
        for i, trade in enumerate(reversed(self.recent_trades)):
            if i >= 5: break
            
            # Format trade based on type
            tick = trade['tick']
            buyer = trade['buyer_id']
            seller = trade['seller_id']
            dA = trade['dA']
            dB = trade['dB']
            dM = trade.get('dM', 0)
            price = trade['price']
            
            # Format barter trade (A<->B only)
            trade_text = f"T{tick}: {buyer} buys {dA}A from {seller} for {dB}B @ {price:.2f}"
            
            trade_label = self.small_font.render(trade_text, True, self.COLOR_TEXT)
            trade_label_width = trade_label.get_width()
            trade_x = self.total_window_width - trade_label_width - 10  # Right-justify each trade line
            self.screen.blit(trade_label, (trade_x, trade_hud_y + 20 + i * 15))
    
    def add_trade_indicator(self, pos: tuple[int, int]):
        """Add a trade indicator at the given position."""
        self.recent_trades.append((self.sim.tick, pos))
    
    def update_trade_history(self):
        """Update trade history from recent trades for exchange rate calculations."""
        # Process recent trades from telemetry
        for trade in self.sim.telemetry.recent_trades_for_renderer:
            tick = trade['tick']
            exchange_pair = trade['exchange_pair_type']
            dA = trade['dA']
            dB = trade['dB']
            dM = trade['dM']
            
            # Calculate exchange rate (barter only: B/A)
            rate = None
            rate_type = None
            
            if exchange_pair == "A<->B" and dA > 0 and dB > 0:
                # B/A rate: units of B per unit of A
                rate = dB / dA
                rate_type = "B/A"
            
            # Add to history if valid
            if rate is not None and rate_type is not None:
                # Check if this trade is already in history
                already_exists = any(
                    h[0] == tick and h[1] == rate_type and abs(h[2] - rate) < 0.0001
                    for h in self.trade_history
                )
                if not already_exists:
                    self.trade_history.append((tick, rate_type, rate))
        
        # Keep only last 1000 trades to prevent memory issues
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
    
    def calculate_exchange_rate_averages(self, rate_type: str) -> dict[str, float | None]:
        """
        Calculate exchange rate averages for different time windows.
        
        Args:
            rate_type: Type of exchange rate ("M/A", "M/B", or "B/A")
            
        Returns:
            Dictionary with keys: 'last_tick', 'last_10', 'last_50', 'lifetime'
            Values are average rates or None if no data available
        """
        current_tick = self.sim.tick
        
        # Filter trades by rate type
        relevant_trades = [(tick, rate) for tick, rtype, rate in self.trade_history if rtype == rate_type]
        
        if not relevant_trades:
            return {
                'last_tick': None,
                'last_10': None,
                'last_50': None,
                'lifetime': None
            }
        
        # Calculate averages for different windows
        result = {}
        
        # Last tick only
        last_tick_trades = [rate for tick, rate in relevant_trades if tick == current_tick]
        result['last_tick'] = sum(last_tick_trades) / len(last_tick_trades) if last_tick_trades else None
        
        # Last 10 ticks
        last_10_trades = [rate for tick, rate in relevant_trades if current_tick - tick < 10]
        result['last_10'] = sum(last_10_trades) / len(last_10_trades) if last_10_trades else None
        
        # Last 50 ticks
        last_50_trades = [rate for tick, rate in relevant_trades if current_tick - tick < 50]
        result['last_50'] = sum(last_50_trades) / len(last_50_trades) if last_50_trades else None
        
        # Lifetime
        all_rates = [rate for _, rate in relevant_trades]
        result['lifetime'] = sum(all_rates) / len(all_rates) if all_rates else None
        
        return result
    
    def draw_left_panel(self):
        """Draw the left info panel with exchange rate information."""
        # Draw background
        pygame.draw.rect(
            self.screen, self.COLOR_PANEL_BACKGROUND,
            (0, 0, self.left_panel_width, self.height)
        )
        
        # Draw separator line
        pygame.draw.line(
            self.screen, self.COLOR_PANEL_BORDER,
            (self.left_panel_width, 0), (self.left_panel_width, self.height),
            2
        )
        
        # Update trade history
        self.update_trade_history()
        
        # Draw title
        y_offset = 10
        title = self.font.render("Exchange Rates", True, self.COLOR_TEXT)
        self.screen.blit(title, (10, y_offset))
        y_offset += 30
        
        # Draw exchange rate information for barter only
        rate_types = [
            ("B/A", "Good B/Good A")
        ]
        
        for rate_type, label in rate_types:
            # Draw section header
            header = self.font.render(label + ":", True, self.COLOR_TEXT)
            self.screen.blit(header, (10, y_offset))
            y_offset += 20
            
            # Calculate averages
            averages = self.calculate_exchange_rate_averages(rate_type)
            
            # Draw each time window
            windows = [
                ("Last Tick", averages['last_tick']),
                ("Last 10", averages['last_10']),
                ("Last 50", averages['last_50']),
                ("Lifetime", averages['lifetime'])
            ]
            
            for window_label, avg in windows:
                if avg is not None:
                    text = f"  {window_label}: {avg:.4f}"
                else:
                    text = f"  {window_label}: --"
                
                label_surface = self.small_font.render(text, True, self.COLOR_TEXT)
                self.screen.blit(label_surface, (10, y_offset))
                y_offset += 15
            
            # Add spacing between sections
            y_offset += 10
        
        # Display agent inventories if fewer than 5 agents
        if len(self.sim.agents) < 5:
            # Add some spacing before inventory section
            y_offset += 20
            
            # Draw inventory section header
            inventory_header = self.font.render("Agent Inventories", True, self.COLOR_TEXT)
            self.screen.blit(inventory_header, (10, y_offset))
            y_offset += 25
            
            # Display each agent's inventory
            for agent in sorted(self.sim.agents, key=lambda a: a.id):
                # Agent ID and position
                agent_info = f"Agent {agent.id} (pos: {agent.pos[0]},{agent.pos[1]}):"
                agent_label = self.small_font.render(agent_info, True, self.COLOR_TEXT)
                self.screen.blit(agent_label, (10, y_offset))
                y_offset += 18
                
                # Inventory values
                inventory_text = f"  A: {agent.inventory.A}, B: {agent.inventory.B}"
                inventory_label = self.small_font.render(inventory_text, True, self.COLOR_TEXT)
                self.screen.blit(inventory_label, (15, y_offset))
                y_offset += 18
                
                # Add small spacing between agents
                y_offset += 5

