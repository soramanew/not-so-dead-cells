import pygame
from enemy.enemy import Enemy
from util.func import normalise_for_drawing, normalise_rect
from util.type import Colour, Rect, Side, Vec2

from ...modifier import DamageMod, Modifier, SpeedMod
from ..weapon import Weapon


class MeleeWeapon(Weapon):
    AVAILABLE_MODS: list[Modifier] = [DamageMod, SpeedMod]

    @property
    def atk_top(self) -> float:
        return self.player.arm_y - self.atk_height / 2

    @property
    def atk_area(self) -> Rect:
        return normalise_rect(
            self.player.arm_x,
            self.atk_top,
            self.atk_width * self.player.facing.value,
            self.atk_height,
        )

    @Weapon.left.getter
    def left(self) -> float:
        return self.player.arm_x - (self.width if self.player.facing is Side.LEFT else 0)

    @Weapon.top.getter
    def top(self) -> float:
        return self.atk_top + (self.atk_height - self.height) * ((self.atk_length - self.atk_time) / self.atk_length)

    def __init__(
        self,
        atk_width: int,
        atk_height: int,
        atk_windup: float,
        atk_length: float,
        kb: Vec2 = (0, 0),
        **kwargs,
    ):
        self.atk_width: int = atk_width  # Width of total attack area
        self.atk_height: int = atk_height  # Height of total attack area
        self.atk_windup: float = atk_windup  # Wind up time
        self.atk_length: float = atk_length  # Length of swing
        self.kb: Vec2 = kb

        # Apply modifiers
        super().__init__(**kwargs)

        self.dps: float = round(self.damage / (self.atk_windup + self.atk_length), 2)
        self.attacking: bool = False

    def start_attack(self) -> None:
        self.attacking = True

    def stop_attack(self) -> None:
        self.attacking = False

    def interrupt(self) -> None:
        self.stop_attack()
        self.atk_time = 0

    def tick(self, dt: float) -> int:
        # Start attack if attacking
        if self.attacking and self.atk_time <= 0:
            self.atk_time = self.atk_windup + self.atk_length

        # Do attack
        damage = 0
        if 0 < self.atk_time <= self.atk_length:
            for enemy in self.player.current_map.get_rect(*self, lambda e: isinstance(e, Enemy)):
                damage += enemy.take_hit(self.damage, kb=self.kb, side=self.player.facing)

        self.atk_time -= dt

        return damage

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

        if self.atk_time <= self.atk_length:
            x, y, width, height = normalise_for_drawing(*self, x_off, y_off, scale)
            if width <= 0 or height <= 0:
                return
            s.set_alpha(180)
            surface.blit(s, (x, y), (0, 0, width, height))
