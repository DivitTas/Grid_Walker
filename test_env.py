from models import GridWalkAction, Actions
from client import GridWalkEnv

print("Testing Grid Walk Environment via HTTP...")

# Connect to the running server
env = GridWalkEnv(base_url="http://localhost:8000")

# Reset
print("\n=== Resetting Environment ===")
result = env.reset()
obs = result.observation
print(f"Agent at: ({obs.agent_row_position}, {obs.agent_col_position})")
print(f"Goal at: ({obs.goal_row_position}, {obs.goal_col_position})")
print(f"Reward: {obs.reward}, Done: {obs.done}")

# Take some steps
test_actions = [Actions.RIGHT, Actions.DOWN, Actions.RIGHT, Actions.DOWN]
for i, action in enumerate(test_actions, 1):
    print(f"\n--- Step {i}: Moving {action.name} ---")
    result = env.step(GridWalkAction(action=action))
    obs = result.observation
    print(f"Agent at: ({obs.agent_row_position}, {obs.agent_col_position})")
    print(f"Reward: {obs.reward:.3f}, Done: {obs.done}")
    
    if obs.done:
        print("🎉 Episode finished!")
        break

env.close()
print("\n=== Test Complete ===")
