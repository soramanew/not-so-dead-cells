import pygame
from enemy.enemy import Enemy
from util.func import normalise_for_drawing, normalise_rect
from util.type import Colour, Rect, Vec2

from ..weapon import Weapon


class MeleeWeapon(Weapon):
    @property
    def atk_top(self) -> float:
        return self.player.arm_y - self.height / 2

    @property
    def atk_area(self) -> Rect:
        return normalise_rect(
            self.player.front,
            self.atk_top,
            self.atk_width * self.player.facing.value,
            self.atk_height,
        )

    def __init__(
        self,
        atk_width: int,
        atk_height: int,
        atk_speed: float,
        atk_length: float,
        kb: Vec2 = (0, 0),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.atk_width: int = atk_width  # Width of total attack area
        self.atk_height: int = atk_height  # Height of total attack area
        self.atk_speed: float = atk_speed + atk_length  # Cooldown
        self.atk_length: float = atk_length  # Length of swing
        self.kb: Vec2 = kb
        self.dps: float = self.damage / self.atk_speed
        self.attacking: bool = False

    def start_attack(self) -> None:
        self.attacking = True

    def stop_attack(self) -> None:
        self.attacking = False

    def interrupt(self) -> None:
        self.stop_attack()
        self.atk_time = 0

    def tick(self, dt: float) -> None:
        # Start attack if attacking
        if self.attacking and self.atk_cd <= 0:
            self.atk_time = self.atk_length
            self.atk_cd = self.atk_speed

        # Do attack
        if self.atk_time > 0 and self.atk_time <= self.atk_length:
            for enemy in self.player.current_map.get_rect(*self, lambda e: isinstance(e, Enemy)):
                enemy.take_hit(self.damage, kb=self.kb, side=self.player.facing)

        self.atk_time -= dt
        self.atk_cd -= dt

    def draw(
        self,
        surface: pygame.Surface,
        colour: Colour,
        x_off: float,
        y_off: float,
        scale: float,
    ) -> None:
        if self.atk_time <= 0:
            return

        x, y, width, height = normalise_for_drawing(*self.atk_area, x_off, y_off, scale)
        if width <= 0 or height <= 0:
            return

        s = pygame.Surface((width, height))
        s.set_alpha(120)
        s.fill(colour)
        surface.blit(s, (x, y))

        x, y, width, height = normalise_for_drawing(*self, x_off, y_off, scale)
        if width <= 0 or height <= 0:
            return
        s.set_alpha(180)
        surface.blit(s, (x, y), (0, 0, width, height))
