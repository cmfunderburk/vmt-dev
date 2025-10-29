"""
Main entry point for VMT simulation with Pygame visualization.
"""

import sys
import os

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import argparse
import pygame
from vmt_engine.simulation import Simulation
from scenarios.loader import load_scenario
from vmt_pygame.renderer import VMTRenderer


def main():
    """Run VMT simulation with visualization."""
    parser = argparse.ArgumentParser(description="Run VMT simulation with visualization.")
    parser.add_argument("scenario_file", nargs="?", default="scenarios/three_agent_barter.yaml",
                        help="Path to the scenario YAML file (e.g., scenarios/three_agent_barter.yaml)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for simulation")

    main_args = parser.parse_args()
    scenario_path = main_args.scenario_file
    
    print(f"Loading scenario: {scenario_path}")
    scenario = load_scenario(scenario_path)
    
    seed = main_args.seed
    
    print(f"Initializing simulation with seed {seed}...")
    sim = Simulation(scenario, seed=seed)
    
    print("Starting visualization...")
    renderer = VMTRenderer(sim)  # Auto-detect optimal cell size
    
    clock = pygame.time.Clock()
    running = True
    paused = False
    tick_rate = 5  # Ticks per second
    
    print("\nControls:")
    print("  SPACE: Pause/Resume")
    print("  R: Reset simulation")
    print("  S: Step one tick (when paused)")
    print("  UP/DOWN: Increase/decrease speed")
    if renderer.needs_scrolling:
        print("  ARROW KEYS: Scroll camera (large grid)")
    print("  T: Toggle trade arrows")
    print("  F: Toggle forage arrows")
    print("  A: All arrows on")
    print("  O: All arrows off")
    print("  [: Toggle left panel")
    print("  ]: Toggle HUD panel")
    print("  M: Toggle money labels")
    print("  L: Toggle lambda heatmap")
    print("  I: Toggle mode/regime overlay")
    print("  K: Toggle market areas")
    print("  J: Toggle market activity")
    print("  Q: Quit")
    print()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                renderer.handle_resize(event.w, event.h)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    print("Paused" if paused else "Resumed")
                
                elif event.key == pygame.K_r:
                    print("Resetting simulation...")
                    sim.close()
                    sim = Simulation(scenario, seed=seed)
                    renderer.sim = sim
                    renderer.recent_trades = sim.telemetry.recent_trades_for_renderer
                    print("Reset complete")
                
                elif event.key == pygame.K_s and paused:
                    print(f"Step: tick {sim.tick}")
                    sim.step()
                
                elif event.key == pygame.K_UP:
                    tick_rate = min(60, tick_rate + 1)
                    print(f"Speed: {tick_rate} ticks/sec")
                
                elif event.key == pygame.K_DOWN:
                    tick_rate = max(1, tick_rate - 1)
                    print(f"Speed: {tick_rate} ticks/sec")
                
                elif event.key == pygame.K_q:
                    running = False
                
                elif event.key == pygame.K_t:
                    # Toggle trade arrows only
                    renderer.show_trade_arrows = not renderer.show_trade_arrows
                    status = "ON" if renderer.show_trade_arrows else "OFF"
                    print(f"Trade arrows: {status}")
                
                elif event.key == pygame.K_f:
                    # Toggle forage arrows only
                    renderer.show_forage_arrows = not renderer.show_forage_arrows
                    status = "ON" if renderer.show_forage_arrows else "OFF"
                    print(f"Forage arrows: {status}")
                
                elif event.key == pygame.K_a:
                    # Toggle all arrows on
                    renderer.show_trade_arrows = True
                    renderer.show_forage_arrows = True
                    print("All arrows: ON")
                
                elif event.key == pygame.K_o:
                    # Toggle all arrows off
                    renderer.show_trade_arrows = False
                    renderer.show_forage_arrows = False
                    print("All arrows: OFF")
                
                elif event.key == pygame.K_m:
                    # Toggle money labels
                    renderer.show_money_labels = not renderer.show_money_labels
                    status = "ON" if renderer.show_money_labels else "OFF"
                    print(f"Money labels: {status}")
                
                elif event.key == pygame.K_l:
                    # Toggle lambda heatmap
                    renderer.show_lambda_heatmap = not renderer.show_lambda_heatmap
                    status = "ON" if renderer.show_lambda_heatmap else "OFF"
                    print(f"Lambda heatmap: {status}")
                
                elif event.key == pygame.K_i:
                    # Toggle mode/regime info overlay
                    renderer.show_mode_regime_overlay = not renderer.show_mode_regime_overlay
                    status = "ON" if renderer.show_mode_regime_overlay else "OFF"
                    print(f"Mode/regime overlay: {status}")
                
                elif event.key == pygame.K_k:
                    # Toggle market areas
                    renderer.show_markets = not renderer.show_markets
                    status = "ON" if renderer.show_markets else "OFF"
                    print(f"Market areas: {status}")
                
                elif event.key == pygame.K_j:
                    # Toggle market activity
                    renderer.show_market_activity = not renderer.show_market_activity
                    status = "ON" if renderer.show_market_activity else "OFF"
                    print(f"Market activity: {status}")
                
                elif event.key == pygame.K_LEFTBRACKET:
                    # Toggle left panel
                    renderer.show_left_panel = not renderer.show_left_panel
                    status = "ON" if renderer.show_left_panel else "OFF"
                    print(f"Left panel: {status}")
                    # Recalculate layout to account for panel visibility change
                    current_size = renderer.screen.get_size()
                    renderer._calculate_layout(current_size[0], current_size[1])
                
                elif event.key == pygame.K_RIGHTBRACKET:
                    # Toggle HUD panel
                    renderer.show_hud_panel = not renderer.show_hud_panel
                    status = "ON" if renderer.show_hud_panel else "OFF"
                    print(f"HUD panel: {status}")
                    # Recalculate layout to account for panel visibility change
                    current_size = renderer.screen.get_size()
                    renderer._calculate_layout(current_size[0], current_size[1])
        
        # Handle camera scrolling (for large grids)
        keys = pygame.key.get_pressed()
        renderer.handle_camera_input(keys)
        
        # Update simulation
        if not paused:
            sim.step()
        
        # Render
        renderer.render()
        
        # Control frame rate
        clock.tick(tick_rate)
    
    sim.close()

    print("\nSimulation ended.")
    print(f"Final tick: {sim.tick}")
    print("Logs saved to ./logs/")
    
    pygame.quit()


if __name__ == "__main__":
    main()

