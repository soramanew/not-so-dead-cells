from math import sqrt

import pygame
from box import Box
from util.func import clamp, get_font

from .map import Map


class DamageNumber(Box):
    REMOVE_THRESHOLD: int = 20

    def __init__(self, damage: int, center_x: float, center_y: float, vx: float, vy: float):
        self.surface: pygame.Surface = get_font(
            "Silkscreen", int(pygame.display.get_window_size()[1] * sqrt(damage)) // 1000 + 16
        ).render(str(damage), True, pygame.Color(168, 208, 204).lerp((228, 59, 54), clamp(damage / 300, 1, 0)))

        super().__init__(center_x - self.surface.width / 2, center_y - self.surface.height / 2, *self.surface.size)

        self.vx: float = vx
        self.vy: float = vy

    def tick(self, dt: float) -> bool:
        if abs(self.vx) < DamageNumber.REMOVE_THRESHOLD or abs(self.vy) < DamageNumber.REMOVE_THRESHOLD:
            return True

        self.vx -= Map.get_air_resistance(self.vx, sqrt(self.height)) * dt * 50
        self.vy -= Map.get_air_resistance(self.vy, sqrt(self.width)) * dt * 50

        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface: pygame.Surface, x_off: float, y_off: float) -> None:
        surface.blit(self.surface, (self.x + x_off, self.y + y_off))
