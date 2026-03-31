# Grid Walk OpenEnv Environment - Copilot Instructions

## Project Overview

This is an OpenEnv environment implementation for grid-based reinforcement learning. OpenEnv is Meta's framework for building and deploying RL environments as HTTP/WebSocket services.

**Architecture**: Client-Server model with three main components:
1. **Environment Logic** (`server/grid_walk_environment.py`) - Implements the `Environment` interface
2. **FastAPI Server** (`server/app.py`) - Exposes environment via HTTP/WebSocket using `create_app()`
3. **Client** (`client.py`) - `EnvClient` subclass that maintains WebSocket connections to the server

## Build & Run Commands

### Local Development
```bash
# Install dependencies (uses uv package manager)
uv sync

# Run server locally
uvicorn server.app:app --reload --port 8000

# Or via project script
uv run server

# Direct environment testing (no server)
python server/grid_walk_environment.py
```

### Docker
```bash
# Build Docker image
docker build -t grid_walk-env:latest -f server/Dockerfile .

# Run container
docker run -p 8000:8000 grid_walk-env:latest
```

### Deployment
```bash
# Deploy to Hugging Face Spaces
openenv push
openenv push --namespace org-name --private
```

## Testing

Tests use pytest (configured in `pyproject.toml`):
```bash
# Install dev dependencies first
uv sync --extra dev

# Run tests (when test files are added)
pytest
pytest tests/test_environment.py  # Single test file
pytest -v                          # Verbose output
pytest --cov                       # With coverage
```

No test files currently exist - add tests to `tests/` directory.

## Key Architecture Patterns

### OpenEnv Three-Layer Model

**Environment Layer** (`server/grid_walk_environment.py`):
- Must implement `reset() -> Observation` and `step(action: Action) -> Observation`
- Must expose `state` property returning `State(episode_id, step_count)`
- Set `SUPPORTS_CONCURRENT_SESSIONS = True` for multi-client support
- Keep environment stateful but isolated per instance

**Server Layer** (`server/app.py`):
- Use `create_app(EnvironmentClass, ActionModel, ObservationModel)` - pass the class, not an instance
- Set `max_concurrent_envs` to control WebSocket session limits
- Server automatically provides: `/reset`, `/step`, `/state`, `/schema`, `/health`, `/docs`, `/web`

**Client Layer** (`client.py`):
- Subclass `EnvClient[ActionType, ObservationType, StateType]`
- Implement three parsing methods:
  - `_step_payload(action) -> Dict` - Convert action to JSON
  - `_parse_result(payload) -> StepResult[Observation]` - Parse step response
  - `_parse_state(payload) -> State` - Parse state response
- Use `from_docker_image()` for automatic container management
- Context manager support for automatic cleanup

### Pydantic Models

**Actions and Observations** (`models.py`):
- Must inherit from `openenv.core.env_server.types.Action` and `Observation`
- Use Pydantic `Field()` for validation and documentation
- Fields auto-generate OpenAPI schemas for the `/docs` endpoint

### Import Pattern for Dual Execution

All modules use try/except for imports to support both:
- Package imports: `from ..models import X` (when installed)
- Direct execution: `from models import X` (when running scripts directly)

## Conventions

### Package Structure
- Root directory doubles as `grid_walk` package (see `pyproject.toml` package-dir mapping)
- `server/` is `grid_walk.server` subpackage
- Keep `__init__.py` files minimal - only export public API

### Running the Environment
- **Development**: `uvicorn` with `--reload` for auto-restart on changes
- **Testing logic**: Run environment file directly to test without server overhead
- **Production**: Use Docker with health checks

### WebSocket vs HTTP
- Client uses WebSocket by default for persistent sessions and lower latency
- HTTP endpoints available for stateless/single-request use cases
- One environment instance per WebSocket connection when using factory mode

### Docker Multi-Stage Build
- Uses `openenv-base` image for consistency
- Builder stage handles `uv sync` with dependency caching
- Final stage copies `.venv` and sets `PYTHONPATH`
- Health check targets `/health` endpoint

## Environment-Specific Notes

This is currently a simple "echo" environment (echoes messages back). The architecture is designed for modification:
- Replace echo logic in `step()` with actual RL environment logic
- Update `GridWalkAction` with relevant action space (e.g., directional moves)
- Update `GridWalkObservation` with state representation (e.g., grid position, goal location)
- Adjust reward calculation in `step()` method
- Update `done` flag based on terminal conditions (goal reached, max steps, etc.)

## Dependencies

- `openenv-core[core]` - Provides FastAPI server and HTTP client types
- `fastapi` and `uvicorn` - Web framework and ASGI server
- Uses `uv` for fast, reproducible dependency management
- `uv.lock` file committed for deterministic builds
