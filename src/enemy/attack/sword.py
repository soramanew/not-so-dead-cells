import pygame
from util.decor import run_once
from util.func import normalise_rect
from util.type import Colour, Rect, Side

from ..enemyabc import EnemyABC


class SwordAttack(EnemyABC):
    @property
    def arm_y(self) -> float:
        return self.y + self.height * self._arm_y

    @property
    def atk_top(self) -> float:
        return self.arm_y - self.atk_height / 2

    @property
    def atk_stop_mv(self) -> bool:
        return self.atk_time > self.atk_length

    def __init__(self, arm_y: float, atk_height: float, atk_height_tick: float):
        self._arm_y: float = arm_y
        self.atk_height: float = atk_height
        self.atk_height_tick: float = atk_height_tick

        self.atk_time: float = 0
        self.atk_cd: float = 0

        # To prevent cd from starting immediately
        self._start_atk_cd.fake_run()

    def _get_atk_area(self) -> Rect:
        return normalise_rect(
            self.front,
            self.atk_top,
            self.atk_width * (1 if self.facing is Side.RIGHT else -1),
            self.atk_height,
        )

    def _get_real_atk_area(self) -> Rect:
        return normalise_rect(
            self.front,
            self.atk_top
            + (self.atk_height - self.atk_height_tick) * ((self.atk_length - self.atk_time) / self.atk_length),
            self.atk_width * (1 if self.facing is Side.RIGHT else -1),
            self.atk_height_tick,
        )

    @run_once
    def _start_atk_cd(self) -> None:
        self.atk_cd = self.atk_speed

    def _tick_attack(self, dt: float) -> None:
        # Warn for attack
        if (
            self.alerted
            and self.atk_time <= 0
            and self.atk_cd <= 0
            and self.player.detect_collision_rect(*self._get_atk_area())
        ):
            self.atk_time = self.atk_windup + self.atk_length
            self._start_atk_cd.reset()

        # Do attack
        if (
            self.atk_time > 0
            and self.atk_time <= self.atk_length
            and self.player.detect_collision_rect(*self._get_real_atk_area())
        ):
            self.player.take_hit(self.damage)

        # Start cooldown when done with attack
        if self.atk_time <= 0:
            self._start_atk_cd()

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

        x, y, width, height = self._get_real_atk_area()
        x = (x + x_off) * scale
        y = (y + y_off) * scale
        width *= scale
        height *= scale
        if x < 0:
            width += x
            x = 0
        if y < 0:
            height += y
            y = 0
        if width < 0 or height < 0:
            return
        s = pygame.Surface((width, height))
        s.set_alpha(128)
        s.fill(colour)
        surface.blit(s, (x, y))
