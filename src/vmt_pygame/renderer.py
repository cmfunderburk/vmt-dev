"""
Pygame visualization for VMT simulation.
"""

import pygame
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vmt_engine.simulation import Simulation
    from vmt_engine.core import Agent


class VMTRenderer:
    """Renders VMT simulation using Pygame."""
    
    def __init__(self, simulation: 'Simulation', cell_size: int = None):
        """
        Initialize renderer with automatic display scaling.
        
        Args:
            simulation: The simulation to render
            cell_size: Size of each grid cell in pixels (None = auto-detect)
        """
        pygame.init()
        
        self.sim = simulation
        
        # Get monitor dimensions
        display_info = pygame.display.Info()
        screen_width = display_info.current_w
        screen_height = display_info.current_h
        
        # Reserve space for margins and HUD
        MARGIN = 80
        HUD_HEIGHT = 100
        available_width = screen_width - (2 * MARGIN)
        available_height = screen_height - (2 * MARGIN) - HUD_HEIGHT
        
        # Calculate optimal cell size if not provided
        if cell_size is None:
            grid_size = simulation.grid.N
            optimal_cell_size = min(
                available_width // grid_size,
                available_height // grid_size
            )
            # Enforce minimum of 10px
            self.cell_size = max(10, optimal_cell_size)
        else:
            self.cell_size = cell_size
        
        # Calculate actual grid dimensions
        grid_pixel_size = simulation.grid.N * self.cell_size
        
        # Determine if scrolling is needed
        self.needs_scrolling = (
            grid_pixel_size > available_width or 
            grid_pixel_size > available_height
        )
        
        # Set window size (capped to available space)
        if self.needs_scrolling:
            self.width = min(grid_pixel_size, available_width)
            self.height = min(grid_pixel_size, available_height)
        else:
            self.width = grid_pixel_size
            self.height = grid_pixel_size
        
        # Store HUD height
        self.hud_height = HUD_HEIGHT
        
        # Add HUD height to total window height
        self.window_height = self.height + HUD_HEIGHT
        
        # Initialize camera offset for scrolling
        self.camera_x = 0
        self.camera_y = 0
        
        # Create window
        self.screen = pygame.display.set_mode((self.width, self.window_height))
        scenario_name = simulation.config.name
        seed = simulation.seed
        pygame.display.set_caption(f"VMT v1 - {scenario_name} (seed: {seed})")
        
        # Scale fonts proportionally (minimum 10px, maximum 16px for base, 8-12px for small)
        base_font_size = max(10, min(16, self.cell_size // 4))
        small_font_size = max(8, min(12, self.cell_size // 5))
        self.font = pygame.font.SysFont('arial', base_font_size)
        self.small_font = pygame.font.SysFont('arial', small_font_size)
        
        # Colors
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_GRAY = (200, 200, 200)
        self.COLOR_LIGHT_GRAY = (240, 240, 240)
        self.COLOR_RED = (255, 100, 100)
        self.COLOR_BLUE = (100, 100, 255)
        self.COLOR_GREEN = (100, 255, 100)
        self.COLOR_PURPLE = (200, 100, 255)
        self.COLOR_YELLOW = (255, 255, 100)
        self.COLOR_ARROW_TRADE = (100, 255, 100)      # Green for trade targeting
        self.COLOR_ARROW_FORAGE = (255, 165, 0)       # Orange for forage targeting
        self.COLOR_ARROW_IDLE_HOME = (173, 216, 230)  # Light blue for idle home targeting
        self.COLOR_IDLE_BORDER = (255, 100, 100)      # Red border for idle agents
        
        # Track trade events for visualization
        self.recent_trades = self.sim.telemetry.recent_trades_for_renderer
        
        # Arrow visualization state
        self.show_trade_arrows = False
        self.show_forage_arrows = False
        
        # Money visualization state
        self.show_money_labels = True  # Toggle with 'M' key
        self.show_lambda_heatmap = False  # Toggle with 'L' key
        self.show_mode_regime_overlay = True  # Toggle with 'I' key
        
        # Money transfer animations
        self.money_sparkles = []  # List of active sparkle animations
        
        # Colors for money
        self.COLOR_GOLD = (255, 215, 0)
        self.COLOR_DARK_GOLD = (218, 165, 32)
    
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
        """Convert grid coordinates to screen coordinates with camera offset."""
        return (
            grid_x * self.cell_size - self.camera_x,
            grid_y * self.cell_size - self.camera_y
        )
    
    def is_visible(self, screen_x, screen_y):
        """Check if coordinates are visible in current viewport."""
        return (
            -self.cell_size <= screen_x <= self.width + self.cell_size and
            -self.cell_size <= screen_y <= self.height + self.cell_size
        )
    
    def render(self):
        """Render the current simulation state."""
        self.screen.fill(self.COLOR_WHITE)
        
        self.draw_grid()
        self.draw_resources()
        self.draw_home_positions()
        
        # Draw agents with optional lambda heatmap coloring
        if self.show_lambda_heatmap:
            self.draw_agents_with_lambda_heatmap()
        else:
            self.draw_agents()
        
        self.draw_target_arrows()
        self.draw_money_labels()
        self.draw_money_sparkles()
        self.draw_trade_indicators()
        self.draw_hud()
        
        pygame.display.flip()
    
    def draw_grid(self):
        """Draw grid lines with camera offset and viewport culling."""
        # Only draw visible grid lines
        start_x = self.camera_x // self.cell_size
        end_x = min(self.sim.grid.N, (self.camera_x + self.width) // self.cell_size + 1)
        start_y = self.camera_y // self.cell_size
        end_y = min(self.sim.grid.N, (self.camera_y + self.height) // self.cell_size + 1)
        
        for x in range(start_x, end_x + 1):
            screen_x = x * self.cell_size - self.camera_x
            pygame.draw.line(
                self.screen, self.COLOR_GRAY,
                (screen_x, 0), (screen_x, self.height),
                1
            )
        
        for y in range(start_y, end_y + 1):
            screen_y = y * self.cell_size - self.camera_y
            pygame.draw.line(
                self.screen, self.COLOR_GRAY,
                (0, screen_y), (self.width, screen_y),
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
                
                # Draw amount label
                label = self.small_font.render(
                    f"{cell.resource.type}:{cell.resource.amount}",
                    True, self.COLOR_BLACK
                )
                self.screen.blit(label, (screen_x + 2, screen_y + 2))
    
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
                self.screen, self.COLOR_BLACK, 
                (home_x, home_y, home_size, home_size)
            )
            pygame.draw.rect(
                self.screen, self.COLOR_LIGHT_GRAY, 
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
        return self.COLOR_BLACK
    
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
        has_money = (
            any(a.inventory.M > 0 for a in agents) or 
            self.sim.params.get('exchange_regime') in ('money_only', 'mixed')
        )
        
        cell_center_x = screen_x + self.cell_size // 2
        cell_bottom_y = screen_y + self.cell_size
        
        if agent_count == 1:
            # Single agent - draw inventory below (current behavior)
            agent = agents[0]
            if has_money:
                inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B} $:{agent.inventory.M}"
            else:
                inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B}"
            
            inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
            inv_width = inv_label.get_width()
            self.screen.blit(inv_label, (cell_center_x - inv_width // 2, cell_bottom_y + 2))
        
        elif agent_count <= 3:
            # 2-3 agents - stack labels vertically
            for idx, agent in enumerate(agents):
                if has_money:
                    inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B} $:{agent.inventory.M}"
                else:
                    inv_text = f"[{agent.id}] A:{agent.inventory.A} B:{agent.inventory.B}"
                
                inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
                inv_width = inv_label.get_width()
                y_offset = cell_bottom_y + 2 + (idx * 12)  # 12px spacing between labels
                
                # Check if label would go off screen
                if y_offset + 12 <= self.height:
                    self.screen.blit(inv_label, (cell_center_x - inv_width // 2, y_offset))
        
        else:
            # 4+ agents - show summary only
            summary_text = f"{agent_count} agents at ({agents[0].pos[0]}, {agents[0].pos[1]})"
            summary_label = self.small_font.render(summary_text, True, self.COLOR_BLACK)
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
                    self.screen, self.COLOR_BLACK, (px, py), radius, 
                    max(1, radius // 5)
                )
                
                # Draw agent ID and utility type label (if space permits)
                if radius >= 5 and self.cell_size >= 15:
                    # Draw agent ID on first line
                    id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
                    id_height = id_label.get_height()
                    
                    # Get utility type label
                    util_type = self.get_utility_type_label(agent)
                    util_label = self.small_font.render(util_type, True, self.COLOR_BLACK)
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
    
    def draw_money_labels(self):
        """Draw money inventory labels near agents (gold text)."""
        if not self.show_money_labels:
            return
        
        # Check if money is active in this simulation
        has_money = self.sim.params.get('exchange_regime') in ('money_only', 'mixed', 'mixed_liquidity_gated')
        if not has_money:
            return
        
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
            
            agent_count = len(agents)
            
            # Draw money label for each agent
            for idx, agent in enumerate(agents):
                # Get display position for this agent
                px, py = self.calculate_agent_display_position(
                    idx, agent_count, cell_center_x, cell_center_y
                )
                
                # Format money value
                money_text = f"${agent.inventory.M}"
                
                # Render as gold text above agent
                money_label = self.small_font.render(money_text, True, self.COLOR_GOLD)
                label_width = money_label.get_width()
                label_height = money_label.get_height()
                
                # Position above the agent with black outline for readability
                label_x = px - label_width // 2
                label_y = py - self.cell_size // 3 - label_height
                
                # Draw black outline
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            outline_label = self.small_font.render(money_text, True, self.COLOR_BLACK)
                            self.screen.blit(outline_label, (label_x + dx, label_y + dy))
                
                # Draw gold text on top
                self.screen.blit(money_label, (label_x, label_y))
    
    def draw_money_sparkles(self):
        """Draw gold sparkle animations for money transfers."""
        # Update and draw active sparkles
        active_sparkles = []
        
        for sparkle in self.money_sparkles:
            # Sparkle format: {'start_pos': (x, y), 'end_pos': (x, y), 'progress': 0.0-1.0, 'amount': M}
            sparkle['progress'] += 0.05  # Animation speed
            
            if sparkle['progress'] < 1.0:
                # Calculate current position (interpolate between start and end)
                start_x, start_y = sparkle['start_pos']
                end_x, end_y = sparkle['end_pos']
                t = sparkle['progress']
                
                curr_x = start_x + (end_x - start_x) * t
                curr_y = start_y + (end_y - start_y) * t
                
                # Draw gold circle (sparkle)
                sparkle_radius = max(3, self.cell_size // 8)
                pygame.draw.circle(
                    self.screen, self.COLOR_GOLD, 
                    (int(curr_x), int(curr_y)), sparkle_radius
                )
                pygame.draw.circle(
                    self.screen, self.COLOR_DARK_GOLD,
                    (int(curr_x), int(curr_y)), sparkle_radius, 1
                )
                
                active_sparkles.append(sparkle)
        
        self.money_sparkles = active_sparkles
    
    def add_money_transfer_animation(self, buyer_pos: tuple[int, int], seller_pos: tuple[int, int], amount: int):
        """
        Add a money sparkle animation from buyer to seller.
        
        Args:
            buyer_pos: (x, y) grid position of buyer
            seller_pos: (x, y) grid position of seller
            amount: Amount of money transferred
        """
        # Convert grid positions to screen positions
        buyer_screen = self.to_screen_coords(*buyer_pos)
        seller_screen = self.to_screen_coords(*seller_pos)
        
        # Calculate cell centers
        buyer_center = (
            buyer_screen[0] + self.cell_size // 2,
            buyer_screen[1] + self.cell_size // 2
        )
        seller_center = (
            seller_screen[0] + self.cell_size // 2,
            seller_screen[1] + self.cell_size // 2
        )
        
        # Add sparkle animation
        self.money_sparkles.append({
            'start_pos': buyer_center,
            'end_pos': seller_center,
            'progress': 0.0,
            'amount': amount
        })
    
    def draw_agents_with_lambda_heatmap(self):
        """
        Draw agents colored by their lambda_money value (heatmap).
        Blue = low lambda, Red = high lambda.
        """
        # Find min/max lambda for normalization
        lambdas = [a.lambda_money for a in self.sim.agents if hasattr(a, 'lambda_money')]
        if not lambdas:
            # Fall back to regular rendering if no lambda data
            self.draw_agents()
            return
        
        min_lambda = min(lambdas)
        max_lambda = max(lambdas)
        lambda_range = max_lambda - min_lambda
        
        if lambda_range == 0:
            lambda_range = 1  # Avoid division by zero
        
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
            
            # Draw each agent in the group with heatmap color
            for idx, agent in enumerate(agents):
                # Get display position for this agent
                px, py = self.calculate_agent_display_position(
                    idx, agent_count, cell_center_x, cell_center_y
                )
                
                # Calculate heatmap color based on lambda
                if hasattr(agent, 'lambda_money'):
                    normalized = (agent.lambda_money - min_lambda) / lambda_range
                    # Blue (low) -> Red (high) gradient
                    red = int(100 + normalized * 155)
                    blue = int(255 - normalized * 155)
                    green = 100
                    color = (red, green, blue)
                else:
                    color = self.COLOR_GRAY
                
                # Draw agent circle
                pygame.draw.circle(self.screen, color, (px, py), radius)
                pygame.draw.circle(
                    self.screen, self.COLOR_BLACK, (px, py), radius,
                    max(1, radius // 5)
                )
                
                # Draw agent ID and utility type label (if space permits)
                if radius >= 5 and self.cell_size >= 15:
                    # Draw agent ID on first line
                    id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
                    id_height = id_label.get_height()
                    
                    # Get utility type label
                    util_type = self.get_utility_type_label(agent)
                    util_label = self.small_font.render(util_type, True, self.COLOR_BLACK)
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
    
    def draw_trade_indicators(self):
        """Draw indicators for recent trades."""
        # This method is now obsolete as trades are drawn on the HUD
        pass
    
    def draw_hud(self):
        """Draw heads-up display with simulation info."""
        hud_y = self.height + 10
        
        # Background for HUD
        pygame.draw.rect(
            self.screen, self.COLOR_LIGHT_GRAY,
            (0, self.height, self.width, self.hud_height)
        )
        
        # Tick counter
        tick_text = f"Tick: {self.sim.tick}"
        tick_label = self.font.render(tick_text, True, self.COLOR_BLACK)
        self.screen.blit(tick_label, (10, hud_y))
        
        # Agent count
        agent_text = f"Agents: {len(self.sim.agents)}"
        agent_label = self.font.render(agent_text, True, self.COLOR_BLACK)
        self.screen.blit(agent_label, (10, hud_y + 20))
        
        # Mode and exchange regime info
        mode = self.sim.current_mode  # "forage", "trade", or "both"
        exchange_regime = self.sim.params.get('exchange_regime', 'barter_only')
        money_scale = self.sim.params.get('money_scale', 1)
        trade_execution_mode = self.sim.params.get('trade_execution_mode', 'minimum')
        
        mode_text = f"Mode: {mode} | Regime: {exchange_regime} | Money Scale: {money_scale} | Trade Execution Mode: {trade_execution_mode}"
        mode_label = self.font.render(mode_text, True, self.COLOR_BLACK)
        self.screen.blit(mode_label, (10, hud_y + 40))
        
        # Total inventory across all agents
        total_A = sum(a.inventory.A for a in self.sim.agents)
        total_B = sum(a.inventory.B for a in self.sim.agents)
        total_M = sum(a.inventory.M for a in self.sim.agents)
        
        # Show average money if any agent has it or money system is active
        has_money = total_M > 0 or self.sim.params.get('exchange_regime') in ('money_only', 'mixed')
        average_money = total_M / len(self.sim.agents) if has_money else 0
        
        if has_money:
            # Format money with explicit comma separators (locale-independent)
            money_str = f"{average_money:,.2f}".replace(',', ',')  # Ensure comma separator
            # Alternative: use manual formatting if locale issues persist
            money_int = int(average_money)
            money_dec = f"{average_money - money_int:.2f}"[1:]  # Get decimal part with leading dot
            money_formatted = f"{money_int:,}{money_dec}"
            inv_text = f"Total Inventory - A: {total_A}  B: {total_B}  Average$: {money_formatted}"
        else:
            inv_text = f"Total Inventory - A: {total_A}  B: {total_B}"
        
        inv_label = self.font.render(inv_text, True, self.COLOR_BLACK)
        self.screen.blit(inv_label, (10, hud_y + 60))
        
        # Controls (with scrolling if needed)
        if self.needs_scrolling:
            controls_text = "SPACE=Pause R=Reset S=Step ←→↑↓=Scroll/Speed T/F/A/O=Arrows M/L/I=Money Q=Quit"
        else:
            controls_text = "SPACE=Pause R=Reset S=Step ↑↓=Speed T/F/A/O=Arrows M/L/I=Money Q=Quit"
        controls_label = self.small_font.render(controls_text, True, self.COLOR_BLACK)
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
        
        arrow_label = self.small_font.render(arrow_status, True, self.COLOR_BLACK)
        self.screen.blit(arrow_label, (10, hud_y + 95))
        
        # Money visualization status
        money_viz_parts = []
        if self.show_money_labels:
            money_viz_parts.append("$Labels")
        if self.show_lambda_heatmap:
            money_viz_parts.append("λHeat")
        if self.show_mode_regime_overlay:
            money_viz_parts.append("Info")
        
        if money_viz_parts:
            money_viz_status = "Money Viz: " + "+".join(money_viz_parts)
        else:
            money_viz_status = "Money Viz: OFF"
        
        money_viz_label = self.small_font.render(money_viz_status, True, self.COLOR_BLACK)
        self.screen.blit(money_viz_label, (200, hud_y + 95))

        # Recent trades (right-justified)
        trade_hud_y = hud_y
        trade_title = self.font.render("Recent Trades:", True, self.COLOR_BLACK)
        trade_title_width = trade_title.get_width()
        trade_x_start = self.width - trade_title_width - 10  # 10px margin from right edge
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
            
            # Determine trade type and format appropriately
            if dM != 0:
                # Monetary trade
                if dA > 0:
                    # Good A for money
                    trade_text = f"T{tick}: {buyer} buys {dA}A from {seller} for ${dM} @ {price:.2f}"
                elif dB > 0:
                    # Good B for money
                    trade_text = f"T{tick}: {buyer} buys {dB}B from {seller} for ${dM} @ {price:.2f}"
                else:
                    trade_text = f"T{tick}: Monetary trade"
            else:
                # Barter trade
                trade_text = f"T{tick}: {buyer} buys {dA}A from {seller} for {dB}B @ {price:.2f}"
            
            trade_label = self.small_font.render(trade_text, True, self.COLOR_BLACK)
            trade_label_width = trade_label.get_width()
            trade_x = self.width - trade_label_width - 10  # Right-justify each trade line
            self.screen.blit(trade_label, (trade_x, trade_hud_y + 20 + i * 15))
    
    def add_trade_indicator(self, pos: tuple[int, int]):
        """Add a trade indicator at the given position."""
        self.recent_trades.append((self.sim.tick, pos))

