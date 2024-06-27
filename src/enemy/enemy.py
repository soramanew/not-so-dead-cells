import random

import pygame
from box import Hitbox
from map import Wall
from util.func import normalise_for_drawing
from util.type import Side, Size, Vec2

from .sense import Sense
from .sprite import Sprite


class Enemy(Hitbox, Sense, Sprite):
    H_BAR_OFF: float = 10
    H_BAR_SIZE: Size = 40, 15
    H_BAR_TIME: float = 10  # The time the health bar is rendered after an enemy is hit (s)
    H_BAR_DAMAGE_DECAY: float = 1.3

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

    @property
    def dead(self) -> bool:
        return self.health <= 0

    def __init__(
        self,
        platform: Wall,  # The platform this enemy is on
        size: Size,
        mass: float,
        sense_size: Size,
        atk_width: float,
        health: int,
        sprite: str,
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
        self.platform: Wall = platform
        self.facing: Side = facing
        self._head_x, self._head_y = head_pos
        self.atk_width: int = atk_width
        self.max_health: int = health
        self.health: int = health
        self.mass: float = mass

        self.alerted: bool = False
        self.stopped: bool = False
        self.i_frames: float = 0
        self.h_bar_time: float = 0
        self.h_bar_damage: float = 0
        self.death_finished: bool = False

        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            sense_x=sense_anchor[0],
            sense_y=sense_anchor[1],
            sense_width=sense_size[0],
            sense_height=sense_size[1],
            folder=sprite,
            **kwargs,
        )

        # After super because depends on height
        self._head_y *= self.height

    def _get_dep_facing(self, ratio: float) -> float:
        return ratio if self.facing is Side.RIGHT else 1 - ratio

    def tick(self, dt: float) -> None:
        if self.dead:
            self.h_bar_time = 0
        else:
            self._tick_sense()
            self._tick_move(dt)
            self._tick_attack(dt)
            self.i_frames -= dt
            self.h_bar_time -= dt
            self.h_bar_damage -= self.h_bar_damage * Enemy.H_BAR_DAMAGE_DECAY * dt

        self._tick_sprite(dt)

    def take_hit(self, damage: int, **kwargs) -> int:
        if self.i_frames <= 0:
            self.i_frames = self.I_FRAMES
            return self._take_hit(damage, **kwargs)
        return 0

    def _take_hit(self, damage: int, kb: Vec2 = None, side: Side = None, **kwargs) -> int:
        """Called when an enemy takes a hit.

        Parameters
        ----------
        damage : int
            The damage done in the hit.
        kb : Vec2, optional
            The knockback done in the hit.
        side : Side, optional
            The direction of the knockback.

        Returns
        -------
        int
            The damage taken due to the hit. This can be different to the given damage due to damage reduction, etc.
        """

        if damage > self.health:
            damage = self.health
        self.h_bar_time = Enemy.H_BAR_TIME
        self.h_bar_damage += damage
        self.health -= damage
        print(f"[DEBUG] {self.__class__.__name__} hit: {self.health}")
        if kb is not None:
            if side is not None:
                self.vx += kb[0] * side.value
            self.vy += kb[1]
        return damage

    def draw_health_bar(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0, scale: float = 1) -> None:
        if self.h_bar_time <= 0:
            return

        h_bar_rect = (
            self.center_x - Enemy.H_BAR_SIZE[0] / 2,
            self.top - Enemy.H_BAR_OFF - Enemy.H_BAR_SIZE[1],
            *Enemy.H_BAR_SIZE,
        )
        draw_rect = normalise_for_drawing(*h_bar_rect, x_off, y_off, scale)
        if draw_rect[2] <= 0 or draw_rect[3] <= 0:
            return
        surface.fill((50, 50, 50), draw_rect)

        border = 0.8, 0.6
        inner_left = self.center_x - (Enemy.H_BAR_SIZE[0] * border[0]) / 2
        inner_top = self.top - Enemy.H_BAR_OFF - Enemy.H_BAR_SIZE[1] * (border[1] + (1 - border[1]) / 2)
        inner_width = Enemy.H_BAR_SIZE[0] * border[0]
        inner_height = Enemy.H_BAR_SIZE[1] * border[1]

        h_bar_rect = (inner_left, inner_top, inner_width, inner_height)
        draw_rect = normalise_for_drawing(*h_bar_rect, x_off, y_off, scale)
        if draw_rect[2] <= 0 or draw_rect[3] <= 0:
            return
        surface.fill((80, 80, 80), draw_rect)

        h_bar_rect = (
            inner_left,
            inner_top,
            ((self.health + self.h_bar_damage) / self.max_health) * inner_width,
            inner_height,
        )
        draw_rect = normalise_for_drawing(*h_bar_rect, x_off, y_off, scale)
        if draw_rect[2] <= 0 or draw_rect[3] <= 0:
            return
        surface.fill((120, 50, 50), draw_rect)

        h_bar_rect = (inner_left, inner_top, (self.health / self.max_health) * inner_width, inner_height)
        draw_rect = normalise_for_drawing(*h_bar_rect, x_off, y_off, scale)
        if draw_rect[2] <= 0 or draw_rect[3] <= 0:
            return
        surface.fill((240, 10, 10), draw_rect)

    def draw(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0, scale: float = 1) -> None:
        # super().draw(surface, (255, 0, 0), x_off, y_off, scale)
        sprite = self.current_sprite
        surface.blit(
            sprite,
            (self.center_x + x_off - sprite.width / 2, self.y + y_off - (sprite.height - self.height)),
        )
        # self.draw_sense(surface, ((0, 255, 0), (200, 50, 50)), x_off, y_off, scale)
        # self.draw_attack(surface, (165, 30, 30), x_off, y_off, scale)
