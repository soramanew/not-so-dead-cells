from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from box import Hitbox

type Vec2 = tuple[float, float]
type Line = tuple[Vec2, Vec2]
type Size = tuple[int, int]
type Rect = tuple[float, float, int, int]  # Vec2, Size
type Colour = tuple[int, int, int]


class Drawable(ABC):
    @abstractmethod
    def draw(self, surface: pygame.Surface, x_off: float, y_off: float, **kwargs) -> None:
        pass


class Interactable(ABC):
    @abstractmethod
    def interact(self) -> None:
        pass

    @abstractmethod
    def draw_popup(self, surface: pygame.Surface, x_off: float, y_off: float, **kwargs) -> None:
        pass


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
    INTERACT = "interact"
    ATTACK_START = "start_attack"
    ATTACK_STOP = "stop_attack"


class EnemyState(Enum):
    ATTACKING = "attack"
    DEAD = "dead"
    # HURT = "hurt"
    IDLE = "idle"
    WALKING = "walk"


class Collision:
    def __init__(self, direction: Direction, entity: Hitbox):
        self.direction = direction
        self.entity = entity

    def __iter__(self):
        return iter((self.direction, self.entity))
