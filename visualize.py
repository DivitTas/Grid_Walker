"""
Grid Walk Visualizer - See the grid in your terminal!

Displays:
  A = Agent position
  G = Goal position
  X = Obstacle
  . = Empty cell

Usage:
  1. Start server: uv run server --port 8000
  2. Run visualizer: uv run python visualize.py

Controls:
  w/↑ = UP    s/↓ = DOWN
  a/← = LEFT  d/→ = RIGHT
  r = Reset   q = Quit
"""

import json
import sys
import os
from websockets.sync.client import connect

# Action mapping
ACTIONS = {
    'w': 0, 'up': 0,      # UP
    'd': 1, 'right': 1,   # RIGHT
    's': 2, 'down': 2,    # DOWN
    'a': 3, 'left': 3,    # LEFT
}

GRID_SIZE = 10


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def draw_grid(agent_pos, goal_pos, obstacles, reward=None, step_count=0, done=False):
    """Draw the grid to terminal."""
    clear_screen()
    
    print("=" * 30)
    print("    GRID WALK VISUALIZER")
    print("=" * 30)
    print()
    
    # Column numbers
    print("    ", end="")
    for col in range(GRID_SIZE):
        print(f" {col}", end="")
    print()
    print("    " + "─" * (GRID_SIZE * 2 + 1))
    
    for row in range(GRID_SIZE):
        print(f" {row} │", end="")
        for col in range(GRID_SIZE):
            cell = " ."
            
            # Check what's in this cell
            if (row, col) in obstacles:
                cell = " X"
            if (row, col) == goal_pos:
                cell = " G"
            if (row, col) == agent_pos:
                cell = " A"
            # Agent on goal
            if (row, col) == agent_pos and agent_pos == goal_pos:
                cell = " ★"
                
            print(cell, end="")
        print(" │")
    
    print("    " + "─" * (GRID_SIZE * 2 + 1))
    print()
    
    # Legend
    print("Legend: A=Agent  G=Goal  X=Obstacle  ★=Win!")
    print()
    
    # Stats
    print(f"Agent: ({agent_pos[0]}, {agent_pos[1]})  Goal: ({goal_pos[0]}, {goal_pos[1]})")
    print(f"Steps: {step_count}  Obstacles: {len(obstacles)}")
    if reward is not None:
        print(f"Last reward: {reward:+.2f}")
    if done:
        print("\n🎉 EPISODE COMPLETE! Press 'r' to reset.")
    print()
    print("Controls: WASD or arrows to move | R=Reset | Q=Quit")


def get_obstacles_from_server(ws):
    """
    Get obstacles by probing - since obstacles aren't in observation,
    we need to track them ourselves based on failed moves.
    For now, return empty set (obstacles are hidden from agent).
    """
    # Note: In a real scenario, you might want the server to expose obstacles
    # for visualization purposes. For now, this demonstrates partial observability.
    return set()


def main():
    print("Connecting to server at ws://localhost:8000/ws ...")
    
    try:
        ws = connect("ws://localhost:8000/ws")
    except Exception as e:
        print(f"Error: Could not connect to server. Is it running?")
        print(f"Start it with: uv run server --port 8000")
        print(f"\nDetails: {e}")
        return
    
    print("Connected! Starting visualizer...")
    
    # Reset to start
    ws.send(json.dumps({"type": "reset"}))
    response = json.loads(ws.recv())
    obs = response["data"]["observation"]
    
    agent_pos = (obs["agent_row_position"], obs["agent_col_position"])
    goal_pos = (obs["goal_row_position"], obs["goal_col_position"])
    obstacles = set()  # Hidden from agent (partial observability)
    discovered_obstacles = set()  # Obstacles we've bumped into
    
    step_count = 0
    total_reward = 0
    last_reward = None
    done = False
    
    # Initial draw
    draw_grid(agent_pos, goal_pos, discovered_obstacles, last_reward, step_count, done)
    
    # Main loop
    try:
        while True:
            # Get input
            print("\nAction: ", end="", flush=True)
            try:
                user_input = input().lower().strip()
            except EOFError:
                break
            
            if user_input == 'q':
                print("Goodbye!")
                break
            
            if user_input == 'r':
                # Reset
                ws.send(json.dumps({"type": "reset"}))
                response = json.loads(ws.recv())
                obs = response["data"]["observation"]
                
                agent_pos = (obs["agent_row_position"], obs["agent_col_position"])
                goal_pos = (obs["goal_row_position"], obs["goal_col_position"])
                discovered_obstacles = set()
                step_count = 0
                total_reward = 0
                last_reward = None
                done = False
                
                draw_grid(agent_pos, goal_pos, discovered_obstacles, last_reward, step_count, done)
                continue
            
            if done:
                print("Episode done! Press 'r' to reset or 'q' to quit.")
                continue
            
            # Map input to action
            if user_input not in ACTIONS:
                print(f"Unknown command: '{user_input}'. Use WASD, arrows, r, or q.")
                continue
            
            action = ACTIONS[user_input]
            old_pos = agent_pos
            
            # Send action
            ws.send(json.dumps({"type": "step", "data": {"action": action}}))
            response = json.loads(ws.recv())
            
            obs = response["data"]["observation"]
            reward = response["data"]["reward"]
            done = response["data"]["done"]
            
            agent_pos = (obs["agent_row_position"], obs["agent_col_position"])
            step_count += 1
            total_reward += reward
            last_reward = reward
            
            # If we didn't move and got penalty, we hit an obstacle!
            if old_pos == agent_pos and reward < -0.05:
                # Figure out where the obstacle was
                direction_map = {
                    0: (-1, 0),  # UP
                    1: (0, 1),   # RIGHT
                    2: (1, 0),   # DOWN
                    3: (0, -1),  # LEFT
                }
                dr, dc = direction_map[action]
                obstacle_pos = (old_pos[0] + dr, old_pos[1] + dc)
                # Only add if within bounds (otherwise it was a wall hit)
                if 0 <= obstacle_pos[0] < GRID_SIZE and 0 <= obstacle_pos[1] < GRID_SIZE:
                    discovered_obstacles.add(obstacle_pos)
            
            draw_grid(agent_pos, goal_pos, discovered_obstacles, last_reward, step_count, done)
            
            if done:
                print(f"\n🎉 Total reward: {total_reward:+.2f}")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    finally:
        ws.close()


if __name__ == "__main__":
    main()
