from abc import abstractmethod

import pygame
from util.func import normalise_for_drawing
from util.type import Colour, Rect

from ...enemyabc import EnemyABC


class MeleeAttack(EnemyABC):
    @abstractmethod
    def _get_atk_area(self) -> Rect:
        pass

    @abstractmethod
    def _get_real_atk_area(self) -> Rect:
        pass

    @property
    def atk_stop_mv(self) -> bool:
        return self.atk_time > self.atk_length

    def __init__(self, arm_y: float, damage: int, atk_windup: float, atk_speed: float, atk_length: float, **kwargs):
        super().__init__(**kwargs)
        self._arm_y: float = arm_y
        self.damage: int = damage
        self.atk_windup: float = atk_windup
        self.atk_speed: float = atk_speed
        self.atk_length: float = atk_length
        self.atk_time: float = 0
        self.atk_cd: float = 0

    def _tick_attack(self, dt: float) -> None:
        # Warn for attack
        if (
            self.alerted
            and self.atk_time <= 0
            and self.atk_cd <= 0
            and self.player.detect_collision_rect(*self._get_atk_area())
        ):
            self.atk_time = self.atk_windup + self.atk_length
            self.atk_cd = self.atk_speed

        # Do attack
        if (
            self.atk_time > 0
            and self.atk_time <= self.atk_length
            and self.player.detect_collision_rect(*self._get_real_atk_area())
        ):
            self.player.take_hit(self.damage)

        self.atk_time -= dt
        self.atk_cd -= dt

    def draw_attack(
        self,
        surface: pygame.Surface,
        colour: Colour,
        x_off: float,
        y_off: float,
        scale: float,
    ) -> None:
        if self.atk_time <= 0 or self.atk_time > self.atk_length:
            return

        x, y, width, height = normalise_for_drawing(*self._get_atk_area(), x_off, y_off, scale)
        if width <= 0 or height <= 0:
            return

        s = pygame.Surface((width, height))
        s.set_alpha(80)
        s.fill(colour)
        surface.blit(s, (x, y))

        x, y, width, height = normalise_for_drawing(*self._get_real_atk_area(), x_off, y_off, scale)
        if width <= 0 or height <= 0:
            return
        s.set_alpha(150)
        surface.blit(s, (x, y), (0, 0, width, height))
