# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Grid Walk Environment.

The grid_walk environment is a simple environment that navigates a 2D grid with obstacles to reach a goal square.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from enum import Enum

class Actions(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

class GridWalkAction(Action):
    """Action for the Grid Walk environment - Move in specified direction (Up, Down, Left, Right)."""
    action: Actions = Field(...,description="Direction to move") 


class GridWalkObservation(Observation):
    """Observation from the Grid Walk environment - the agent and goal position."""

    agent_row_position :int = Field(...,description="Agent's current row coordinate")
    agent_col_position :int = Field(...,description="Agent's current column coordinate")
    goal_row_position : int = Field(...,description="Goal row coordinate")
    goal_col_position : int = Field(...,description="Goal column coordinate")
