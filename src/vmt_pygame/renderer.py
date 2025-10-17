"""
Pygame visualization for VMT simulation.
"""

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vmt_engine.simulation import Simulation


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
        pygame.display.set_caption("VMT v1 - Virtual Market Testbed")
        
        # Scale fonts proportionally (minimum 8px, maximum 14px for base, 6-10px for small)
        base_font_size = max(8, min(14, self.cell_size // 4))
        small_font_size = max(6, min(10, self.cell_size // 5))
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
        
        # Track trade events for visualization
        self.recent_trades = self.sim.telemetry.recent_trades_for_renderer
    
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
        self.draw_agents()
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
    
    def draw_agents(self):
        """Draw agents as circles with camera offset and viewport culling."""
        for agent in self.sim.agents:
            x, y = agent.pos
            screen_x, screen_y = self.to_screen_coords(x, y)
            
            # Skip if not visible
            if not self.is_visible(screen_x, screen_y):
                continue
            
            # Calculate center position
            px = screen_x + self.cell_size // 2
            py = screen_y + self.cell_size // 2
            
            # Color based on utility type
            if agent.utility:
                utility_type = agent.utility.__class__.__name__
                if utility_type == "UCES":
                    color = self.COLOR_GREEN
                elif utility_type == "ULinear":
                    color = self.COLOR_PURPLE
                else:
                    color = self.COLOR_YELLOW
            else:
                color = self.COLOR_BLACK
            
            # Draw agent circle
            radius = max(3, self.cell_size // 3)  # Minimum radius of 3px
            pygame.draw.circle(self.screen, color, (px, py), radius)
            pygame.draw.circle(self.screen, self.COLOR_BLACK, (px, py), radius, max(1, radius // 5))
            
            # Draw agent ID (only if cell size is large enough)
            if self.cell_size >= 15:
                id_label = self.small_font.render(str(agent.id), True, self.COLOR_BLACK)
                id_rect = id_label.get_rect(center=(px, py))
                self.screen.blit(id_label, id_rect)
            
            # Draw inventory below agent (only if cell size is large enough)
            if self.cell_size >= 20:
                inv_text = f"A:{agent.inventory.A} B:{agent.inventory.B}"
                inv_label = self.small_font.render(inv_text, True, self.COLOR_BLACK)
                inv_width = inv_label.get_width()
                self.screen.blit(inv_label, (px - inv_width // 2, py + radius + 2))
    
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
        
        # Total inventory across all agents
        total_A = sum(a.inventory.A for a in self.sim.agents)
        total_B = sum(a.inventory.B for a in self.sim.agents)
        inv_text = f"Total Inventory - A: {total_A}  B: {total_B}"
        inv_label = self.font.render(inv_text, True, self.COLOR_BLACK)
        self.screen.blit(inv_label, (10, hud_y + 40))
        
        # Controls (with scrolling if needed)
        if self.needs_scrolling:
            controls_text = "SPACE=Pause R=Reset S=Step ←→↑↓=Scroll/Speed Q=Quit"
        else:
            controls_text = "Controls: SPACE=Pause  R=Reset  S=Step  ↑↓=Speed  Q=Quit"
        controls_label = self.small_font.render(controls_text, True, self.COLOR_BLACK)
        self.screen.blit(controls_label, (10, hud_y + 60))

        # Recent trades
        trade_hud_y = hud_y
        trade_title = self.font.render("Recent Trades:", True, self.COLOR_BLACK)
        self.screen.blit(trade_title, (250, trade_hud_y))
        for i, trade in enumerate(reversed(self.recent_trades)):
            if i >= 5: break
            trade_text = (
                f"T{trade['tick']}: {trade['buyer_id']} buys {trade['dA']}A from {trade['seller_id']} "
                f"for {trade['dB']}B @ {trade['price']:.2f}"
            )
            trade_label = self.small_font.render(trade_text, True, self.COLOR_BLACK)
            self.screen.blit(trade_label, (250, trade_hud_y + 20 + i * 15))
    
    def add_trade_indicator(self, pos: tuple[int, int]):
        """Add a trade indicator at the given position."""
        self.recent_trades.append((self.sim.tick, pos))

