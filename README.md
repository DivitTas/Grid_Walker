---
title: Grid Walk Environment Server
emoji: 🔔
colorFrom: yellow
colorTo: gray
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Grid Walk Environment

A reinforcement learning environment where an agent navigates a 10×10 grid to reach a goal position while avoiding obstacles. The agent can move in four directions (UP, DOWN, LEFT, RIGHT) and receives rewards based on its actions.

## Quick Start

The simplest way to use the Grid Walk environment is through the `GridWalkEnv` class:

```python
from grid_walk import GridWalkAction, GridWalkEnv, Actions

try:
    # Create environment from Docker image
    grid_walkenv = GridWalkEnv.from_docker_image("grid_walk-env:latest")

    # Reset the environment
    result = grid_walkenv.reset()
    print(f"Agent starts at: ({result.observation.agent_row_position}, {result.observation.agent_col_position})")
    print(f"Goal location: ({result.observation.goal_row_position}, {result.observation.goal_col_position})")

    # Navigate towards the goal
    actions = [Actions.RIGHT, Actions.DOWN, Actions.RIGHT, Actions.DOWN]

    for action in actions:
        result = grid_walkenv.step(GridWalkAction(action=action))
        print(f"Action: {action.name}")
        print(f"  → Agent position: ({result.observation.agent_row_position}, {result.observation.agent_col_position})")
        print(f"  → Reward: {result.reward}")
        print(f"  → Done: {result.observation.done}")
        
        if result.observation.done:
            print("Episode complete!")
            break

finally:
    # Always clean up
    grid_walkenv.close()
```

That's it! The `GridWalkEnv.from_docker_image()` method handles:
- Starting the Docker container
- Waiting for the server to be ready
- Connecting to the environment
- Container cleanup when you call `close()`

## Building the Docker Image

Before using the environment, you need to build the Docker image:

```bash
# From project root
docker build -t grid_walk-env:latest -f server/Dockerfile .
```

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --namespace my-org --private
```

The `openenv push` command will:
1. Validate that the directory is an OpenEnv environment (checks for `openenv.yaml`)
2. Prepare a custom build for Hugging Face Docker space (enables web interface)
3. Upload to Hugging Face (ensuring you're logged in)

### Prerequisites

- Authenticate with Hugging Face: The command will prompt for login if not already authenticated

### Options

- `--directory`, `-d`: Directory containing the OpenEnv environment (defaults to current directory)
- `--repo-id`, `-r`: Repository ID in format 'username/repo-name' (defaults to 'username/env-name' from openenv.yaml)
- `--base-image`, `-b`: Base Docker image to use (overrides Dockerfile FROM)
- `--private`: Deploy the space as private (default: public)

### Examples

```bash
# Push to your personal namespace (defaults to username/env-name from openenv.yaml)
openenv push

# Push to a specific repository
openenv push --repo-id my-org/my-env

# Push with a custom base image
openenv push --base-image ghcr.io/meta-pytorch/openenv-base:latest

# Push as a private space
openenv push --private

# Combine options
openenv push --repo-id my-org/my-env --base-image custom-base:latest --private
```

After deployment, your space will be available at:
`https://huggingface.co/spaces/<repo-id>`

The deployed space includes:
- **Web Interface** at `/web` - Interactive UI for exploring the environment
- **API Documentation** at `/docs` - Full OpenAPI/Swagger interface
- **Health Check** at `/health` - Container health monitoring
- **WebSocket** at `/ws` - Persistent session endpoint for low-latency interactions

## Environment Details

### Action
**GridWalkAction**: Contains a single field
- `action` (Actions enum) - Direction to move: UP, DOWN, LEFT, or RIGHT

### Observation
**GridWalkObservation**: Contains the agent's state and environment information
- `agent_row_position` (int) - Agent's current row coordinate (0-9)
- `agent_col_position` (int) - Agent's current column coordinate (0-9)
- `goal_row_position` (int) - Goal's row coordinate (0-9)
- `goal_col_position` (int) - Goal's column coordinate (0-9)
- `reward` (float) - Reward received for the current step
- `done` (bool) - Whether the episode has ended

### Reward Structure
- **Valid move**: -0.01 (encourages efficiency)
- **Invalid move** (wall or obstacle): -0.1 (penalty)
- **Reaching goal**: +1.0 (success!)
- Episode ends after 100 steps or when goal is reached

### Grid Layout
- **Size**: 10×10 grid (rows and columns indexed 0-9)
- **Start position**: Agent always starts at (0, 0)
- **Goal position**: Randomly placed, never at start position
- **Obstacles**: 1-10 obstacles randomly placed, avoiding start and goal positions

## Advanced Usage

### Connecting to an Existing Server

If you already have a Grid Walk environment server running, you can connect directly:

```python
from grid_walk import GridWalkEnv, GridWalkAction, Actions

# Connect to existing server
grid_walkenv = GridWalkEnv(base_url="<ENV_HTTP_URL_HERE>")

# Use as normal
result = grid_walkenv.reset()
result = grid_walkenv.step(GridWalkAction(action=Actions.RIGHT))
```

Note: When connecting to an existing server, `grid_walkenv.close()` will NOT stop the server.

### Using the Context Manager

The client supports context manager usage for automatic connection management:

```python
from grid_walk import GridWalkAction, GridWalkEnv, Actions

# Connect with context manager (auto-connects and closes)
with GridWalkEnv(base_url="http://localhost:8000") as env:
    result = env.reset()
    print(f"Start: ({result.observation.agent_row_position}, {result.observation.agent_col_position})")
    
    # Navigate the grid
    for action in [Actions.RIGHT, Actions.DOWN, Actions.RIGHT]:
        result = env.step(GridWalkAction(action=action))
        print(f"Position: ({result.observation.agent_row_position}, {result.observation.agent_col_position}), Reward: {result.reward}")
```

The client uses WebSocket connections for:
- **Lower latency**: No HTTP connection overhead per request
- **Persistent session**: Server maintains your environment state
- **Efficient for episodes**: Better for many sequential steps

### Concurrent WebSocket Sessions

The server supports multiple concurrent WebSocket connections. To enable this,
modify `server/app.py` to use factory mode:

```python
# In server/app.py - use factory mode for concurrent sessions
app = create_app(
    GridWalkEnvironment,  # Pass class, not instance
    GridWalkAction,
    GridWalkObservation,
    max_concurrent_envs=4,  # Allow 4 concurrent sessions
)
```

Then multiple clients can connect simultaneously:

```python
from grid_walk import GridWalkAction, GridWalkEnv, Actions
from concurrent.futures import ThreadPoolExecutor
import random

def run_episode(client_id: int):
    with GridWalkEnv(base_url="http://localhost:8000") as env:
        result = env.reset()
        total_reward = 0
        
        while not result.observation.done:
            # Simple random policy
            action = random.choice([Actions.UP, Actions.DOWN, Actions.LEFT, Actions.RIGHT])
            result = env.step(GridWalkAction(action=action))
            total_reward += result.reward
            
        return client_id, total_reward

# Run 4 episodes concurrently
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(run_episode, range(4)))
    for client_id, total_reward in results:
        print(f"Client {client_id}: Total reward = {total_reward}")
```

## Development & Testing

### Direct Environment Testing

Test the environment logic directly without starting the HTTP server:

```bash
# From the project root
python3 server/grid_walk_environment.py
```

This verifies that:
- Environment resets correctly with agent at (0,0) and random goal/obstacles
- Step executes movement actions properly
- Invalid moves (walls/obstacles) are handled with appropriate penalties
- Goal reaching terminates the episode with positive reward
- State tracking works across multiple steps

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

## Project Structure

```
grid_walk/
├── .dockerignore         # Docker build exclusions
├── __init__.py            # Module exports
├── README.md              # This file
├── openenv.yaml           # OpenEnv manifest
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependencies (generated)
├── client.py              # GridWalkEnv client
├── models.py              # Action and Observation models
└── server/
    ├── __init__.py        # Server module exports
    ├── grid_walk_environment.py  # Core environment logic
    ├── app.py             # FastAPI application (HTTP + WebSocket endpoints)
    └── Dockerfile         # Container image definition
```
