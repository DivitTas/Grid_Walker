"""
WebSocket test script for Grid Walk environment.

This script connects to the environment server via WebSocket,
maintaining a persistent connection so the environment state
is preserved across reset() and step() calls.
"""

import sys
import json
from websockets.sync.client import connect

# Import models directly
from models import Actions, GridWalkAction, GridWalkObservation

def parse_observation(obs_data):
    """Parse observation data from server response."""
    return GridWalkObservation(
        agent_row_position=obs_data["agent_row_position"],
        agent_col_position=obs_data["agent_col_position"],
        goal_row_position=obs_data["goal_row_position"],
        goal_col_position=obs_data["goal_col_position"],
        metadata=obs_data.get("metadata", {})
    )

def main():
    # Create WebSocket connection directly
    ws = connect("ws://localhost:8000/ws")
    
    print("=" * 50)
    print("Grid Walk WebSocket Test")
    print("=" * 50)
    
    # Reset environment - starts a new episode
    ws.send(json.dumps({"type": "reset"}))
    response = json.loads(ws.recv())
    obs = parse_observation(response["data"]["observation"])
    
    print(f"\n[RESET] New episode started!")
    print(f"  Agent position: ({obs.agent_row_position}, {obs.agent_col_position})")
    print(f"  Goal position:  ({obs.goal_row_position}, {obs.goal_col_position})")
    
    # Run a simple episode with fixed actions
    actions_to_try = [
        Actions.RIGHT,
        Actions.RIGHT,
        Actions.DOWN,
        Actions.DOWN,
        Actions.LEFT,
        Actions.UP,
    ]
    
    print(f"\n[EPISODE] Taking {len(actions_to_try)} steps...")
    print("-" * 50)
    
    total_reward = 0
    for i, action in enumerate(actions_to_try):
        # Send step message - action value directly  
        ws.send(json.dumps({
            "type": "step",
            "data": {"action": action.value}
        }))
        response = json.loads(ws.recv())
        
        obs = parse_observation(response["data"]["observation"])
        reward = response["data"]["reward"]
        done = response["data"]["done"]
        total_reward += reward
        
        print(f"Step {i+1}: {action.name:5} -> "
              f"Agent at ({obs.agent_row_position}, {obs.agent_col_position}), "
              f"reward={reward:+.2f}, done={done}")
        
        if done:
            print(f"\n[DONE] Episode finished! Goal reached!")
            break
    
    print("-" * 50)
    print(f"Total reward: {total_reward:+.2f}")
    
    # Test reset again to show state persistence works
    print(f"\n[RESET] Starting another episode...")
    ws.send(json.dumps({"type": "reset"}))
    response = json.loads(ws.recv())
    obs = parse_observation(response["data"]["observation"])
    print(f"  Agent position: ({obs.agent_row_position}, {obs.agent_col_position})")
    print(f"  Goal position:  ({obs.goal_row_position}, {obs.goal_col_position})")
    print("  (Notice: goal may be different - new random goal each reset!)")
    
    # Close WebSocket connection
    ws.close()
    
    print("\n" + "=" * 50)
    print("WebSocket test complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
