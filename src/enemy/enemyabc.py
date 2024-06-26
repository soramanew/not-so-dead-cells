from abc import abstractmethod

import pygame
from box import BoxABC
from map import Map, Wall
from player import Player
from util.type import Colour, EnemyState, Side


class EnemyABC(BoxABC):
    I_FRAMES: float

    player: Player
    map: Map
    platform: Wall
    facing: Side
    atk_width: int
    atk_windup: float
    atk_speed: float
    atk_length: float
    mass: float
    health: int
    damage: int
    alerted: bool
    vx: float
    vy: float
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
    def atk_stop_mv(self) -> bool:
        """If the enemy is stopped due to attacking."""
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
