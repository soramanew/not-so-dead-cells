from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

import pygame
from box import BoxABC
from map import Wall
from util.type import Colour, EnemyState, Side

if TYPE_CHECKING:
    from .sprite import State


class EnemyABC(BoxABC):
    I_FRAMES: float

    platform: Wall
    facing: Side
    atk_width: int
    atk_windup: float
    atk_speed: float
    atk_length: float
    attacking: bool
    mass: float
    health: int
    damage: int
    alerted: bool
    can_sense_player: bool
    vx: float
    vy: float
    states: dict[str, State]
    state: EnemyState
    death_finished: bool

    @property
    @abstractmethod
    def head_x(self) -> float:
        pass

    @property
    @abstractmethod
    def head_y(self) -> float:
        pass

    @property
    @abstractmethod
    def front(self) -> float:
        pass

    @property
    @abstractmethod
    def arm_y(self) -> float:
        pass

    @property
    @abstractmethod
    def alerting(self) -> bool:
        pass

    @property
    @abstractmethod
    def current_sprite(self) -> pygame.Surface:
        pass

    @property
    @abstractmethod
    def dead(self) -> bool:
        pass

    @abstractmethod
    def _get_dep_facing(self, ratio: float) -> float:
        pass

    @abstractmethod
    def _tick_sense(self, dt: float) -> None:
        pass

    @abstractmethod
    def _tick_move(self) -> None:
        pass

    @abstractmethod
    def _tick_attack(self, dt: float) -> None:
        pass

    @abstractmethod
    def draw_attack(self, surface: pygame.Surface, colour: Colour, x_off: float, y_off: float, scale: float) -> None:
        pass
