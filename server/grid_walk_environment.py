# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Grid Walk Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""
import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import GridWalkAction, GridWalkObservation, Actions
except ImportError:
    from models import GridWalkAction, GridWalkObservation, Actions


class GridWalkEnvironment(Environment):
    """
    A simple echo environment that echoes back messages.

    This environment is designed for testing the HTTP server infrastructure.
    It maintains minimal state and simply echoes back whatever message it receives.

    Example:
        >>> env = GridWalkEnvironment()
        >>> obs = env.reset()
        >>> print(obs.echoed_message)  # "Grid Walk environment ready!"
        >>>
        >>> obs = env.step(GridWalkAction(message="Hello"))
        >>> print(obs.echoed_message)  # "Hello"
        >>> print(obs.message_length)  # 5
    """

    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    GRID_SIZE = 10
    MAX_STEPS = 100

    def __init__(self):
        """Initialize the grid_walk environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0
        self.agent_row = 0
        self.agent_col = 0
        self.goal_row = 0
        self.goal_col = 0
        self.obstacles = set()


    def reset(self) -> GridWalkObservation:
        """
        Reset the environment.

        Returns:
            GridWalkObservation with a ready message
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count += 1
        self.agent_col = 0
        self.agent_row = 0
        self.goal_row = random.randint(0,9)
        self.goal_col = random.randint(0,9)
        while(self.goal_col ==0 and self.goal_row ==0):
            self.goal_row = random.randint(0,9)
            self.goal_col = random.randint(0,9)
        num_obstacles = random.randint(1,10)
        self.obstacles = set()
        while len(self.obstacles) < num_obstacles:
            obs_row = random.randint(0,9)
            obs_col = random.randint(0,9)

            if (obs_row,obs_col) == (0,0):
                continue
            if (obs_row,obs_col) == (self.goal_row,self.goal_col):
                continue
            self.obstacles.add((obs_row,obs_col))

        return GridWalkObservation(
            agent_row_position = self.agent_row,
            agent_col_position = self.agent_col,
            goal_row_position = self.goal_row,
            goal_col_position = self.goal_col,
            done=False,
            reward = 0.0,
        )

    def step(self, action: GridWalkAction) -> GridWalkObservation:  # type: ignore[override]
        """
        Execute a step in the environment by moving in a direction.

        Args:
            action: GridWalkAction containing the direction to move

        Returns:
            GridWalkObservation with the goal position and agent position
        """
        self._state.step_count += 1

        
        direction = {
            Actions.UP: (-1,0),
            Actions.DOWN: (1,0),
            Actions.LEFT: (0,-1),
            Actions.RIGHT: (0,1)
        }
        delta_row, delta_col = direction[action.action]
        new_row = self.agent_row + delta_row
        new_col = self.agent_col + delta_col
        IS_VALID = True
        done = False
        reward = 0
        if new_row<0 or new_row>= self.GRID_SIZE or new_col<0 or new_col>=self.GRID_SIZE:
            IS_VALID=False
        if (new_row,new_col) in self.obstacles:
            IS_VALID=False
        if(IS_VALID):
            self.agent_col = new_col
            self.agent_row = new_row
            reward = -0.01
        else:
            reward = -0.1
              
        if self.agent_row == self.goal_row and self.agent_col == self.goal_col:
            reward = 1.0
            done = True

        if self.state.step_count >= self.MAX_STEPS:
            done = True
        return GridWalkObservation(
            agent_row_position = self.agent_row,
            agent_col_position = self.agent_col,
            goal_row_position = self.goal_row,
            goal_col_position = self.goal_col,
            done=done,
            reward=reward,
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
