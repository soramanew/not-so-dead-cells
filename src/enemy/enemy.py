import random

import pygame
from box import Hitbox
from map import Map, Wall
from player import Player
from util.type import Side, Size, Vec2

from .sense import Sense


class Enemy(Hitbox, Sense):
    @property
    def head_x(self) -> float:
        return self.x + self._get_dep_facing(self._head_x) * self.width

    @property
    def head_y(self) -> float:
        return self.y + self._head_y

    @property
    def front(self) -> float:
        return self.left if self.facing is Side.LEFT else self.right

    @property
    def arm_y(self) -> float:
        return self.y + self.height * self._arm_y

    def __init__(
        self,
        player: Player,
        current_map: Map,
        platform: Wall,  # The platform this enemy is on
        size: Size,
        sense_size: Size,
        atk_width: float,
        health: int,
        pos: Vec2 = (None, None),
        facing: Side = None,
        head_pos: Vec2 = (0.7, 0.3),  # Head position in direction facing as ratio (width, height)
        sense_anchor: Vec2 = (0.2, 0.5),  # Same as head but for sense
        **kwargs,
    ):
        width, height = size
        x, y = pos

        # Default values
        if x is None:
            x = random.uniform(platform.left, platform.right - width)
        if y is None:
            y = platform.top - height
        if facing is None:
            facing = Side.RIGHT if random.getrandbits(1) else Side.LEFT  # Random init dir

        # Init
        self.player: Player = player
        self.map: Map = current_map
        self.platform: Wall = platform
        self.facing: Side = facing
        self._head_x, self._head_y = head_pos
        self.atk_width: int = atk_width
        self.health: int = health

        self.alerted: bool = False
        self.stopped: bool = False

        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            sense_x=sense_anchor[0],
            sense_y=sense_anchor[1],
            sense_width=sense_size[0],
            sense_height=sense_size[1],
            **kwargs,
        )

        # After super because depends on height
        self._head_y *= self.height

    def _get_dep_facing(self, ratio: float) -> float:
        return ratio if self.facing is Side.RIGHT else 1 - ratio

    def tick(self, dt: float) -> None:
        self._tick_sense()
        self._tick_move(dt)
        self._tick_attack(dt)
        # TODO iframes

    def draw(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0, scale: float = 1) -> None:
        super().draw(surface, (255, 0, 0), x_off, y_off, scale)
        self.draw_sense(surface, ((0, 255, 0), (200, 50, 50)), x_off, y_off, scale)
        self.draw_attack(surface, (165, 30, 30), x_off, y_off, scale)
