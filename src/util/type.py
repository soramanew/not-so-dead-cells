from __future__ import annotations

from enum import Enum
from functools import wraps
from types import MethodType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from box import Hitbox

type Position = tuple[float, float]
type Rect = tuple[float, float, int, int]


class Side(Enum):
    LEFT = -1
    RIGHT = 1


class Direction(Enum):
    LEFT = Side.LEFT
    RIGHT = Side.RIGHT
    UP = -1
    DOWN = 1


class PlayerControl(Enum):
    LEFT = Side.LEFT
    RIGHT = Side.RIGHT
    JUMP = "jump"
    ROLL = "roll"
    SLAM = "slam"


class Collision:
    def __init__(self, direction: Direction, entity: Hitbox):
        self.direction = direction
        self.entity = entity

    def __iter__(self):
        return iter((self.direction, self.entity))


def _reset_run_once(self):
    self.has_run = False


def run_once(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    wrapper.reset = MethodType(_reset_run_once, wrapper)
    return wrapper
