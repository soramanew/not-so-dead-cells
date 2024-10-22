from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from box import Hitbox

type Vec2 = tuple[float, float] | list[float]
type Line = tuple[Vec2, Vec2] | list[Vec2]
type Size = tuple[int, int] | list[int]  # TODO use frects, get rid of int size
type Rect = tuple[float, float, int, int] | list[float]  # Vec2, Size
type Colour = tuple[int, int, int] | list[int]


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


class PlayerState(Enum):
    ATTACKING = "attack"
    DEAD = "dead"
    # HURT = "hurt"
    IDLE = "idle"
    WALKING = "walk"
    SPRINTING = "sprint"
    JUMPING = "jump"
    CLIMBING = "climb"
    WALL_SLIDING = "wall_slide"
    ROLLING = "roll"


class EnemyState(Enum):
    ATTACKING = "attack"
    DEAD = "dead"
    HURT = "hurt"
    IDLE = "idle"
    WALKING = "walk"
    SPRINTING = "sprint"
    ALERTED = "alerted"


class Collision:
    def __init__(self, direction: Direction, entity: Hitbox):
        self.direction = direction
        self.entity = entity

    def __iter__(self):
        return iter((self.direction, self.entity))


class Sound(pygame.mixer.Sound):
    def __init__(self, *args, volume: float = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_volume(volume)
        self.playing: bool = False

    def play(self, *args, **kwargs):
        super().play(*args, **kwargs)
        self.playing = True

    def stop(self):
        super().stop()
        self.playing = False

    def fadeout(self, time: int):
        super().fadeout(time)
        self.playing = False
