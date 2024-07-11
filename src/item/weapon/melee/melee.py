import pygame
import state
from enemy.enemy import Enemy
from util.func import get_project_root, normalise_rect
from util.type import Colour, Rect, Side, Sound, Vec2

from ...modifier import DamageMod, Modifier, SpeedMod
from ..weapon import Weapon
from .sprite import Sprite


class MeleeWeapon(Weapon):
    AVAILABLE_MODS: list[Modifier] = [DamageMod, SpeedMod]

    @property
    def atk_top(self) -> float:
        return state.player.arm_y - self.atk_height / 2

    @property
    def atk_area(self) -> Rect:
        return normalise_rect(
            state.player.arm_x,
            self.atk_top,
            self.atk_width * state.player.facing.value,
            self.atk_height,
        )

    @Weapon.left.getter
    def left(self) -> float:
        return state.player.arm_x - (self.width if state.player.facing is Side.LEFT else 0)

    @Weapon.top.getter
    def top(self) -> float:
        return self.atk_top + (self.atk_height - self.height) * ((self.atk_length - self.atk_time) / self.atk_length)

    def __init__(
        self,
        sprite: str,
        sprite_frames: int,
        atk_width: int,
        atk_height: int,
        atk_windup: float,
        atk_length: float,
        kb: Vec2 = (0, 0),
        sprite_speed: float = 1,
        **kwargs,
    ):
        sprite = f"weapons/{sprite}"
        self.sprite: str = f"{sprite}_Icon"
        self.sprite_obj: Sprite = Sprite(sprite, sprite_frames, sprite_speed)
        self.atk_width: int = atk_width  # Width of total attack area
        self.atk_height: int = atk_height  # Height of total attack area
        self.atk_windup: float = atk_windup  # Wind up time
        self.atk_length: float = atk_length  # Length of swing
        self.kb: Vec2 = kb

        self._surface: pygame.Surface = pygame.Surface((atk_width, atk_height)).convert()
        self.sfx: Sound = Sound(get_project_root() / "assets/sfx/player/Attack.wav")

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
        self.sfx.fadeout(200)

    def tick(self, dt: float) -> int:
        # Start attack if attacking
        if self.attacking and self.atk_time <= 0:
            self.atk_time = self.atk_windup + self.atk_length
            self.sprite_obj.time = 0

        # Do attack
        damage = int(self.damage * state.player.damage_mul)  # Apply player damage multiplier
        damage_dealt = 0
        if 0 < self.atk_time <= self.atk_length:
            if not self.sfx.playing:
                self.sfx.play(-1)
            for enemy in state.current_map.get_rect(*self, lambda e: isinstance(e, Enemy)):
                damage_dealt += enemy.take_hit(damage, kb=self.kb, side=state.player.facing)

        if self.atk_time <= 0:
            self.sfx.fadeout(200)

        self.atk_time -= dt
        self.sprite_obj.tick(dt)

        return damage_dealt

    def draw(
        self,
        surface: pygame.Surface,
        colour: Colour,
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        if self.atk_time <= 0:
            return

        # from util.func import normalise_for_drawing

        # x, y, width, height = normalise_for_drawing(*self.atk_area, x_off, y_off, scale)
        # if width <= 0 or height <= 0:
        #     return

        # self._surface.set_alpha(120)
        # self._surface.fill(colour)
        # surface.blit(self._surface, (x, y))

        # if self.atk_time <= self.atk_length:
        #     x, y, width, height = normalise_for_drawing(*self, x_off, y_off, scale)
        #     if width <= 0 or height <= 0:
        #         return
        #     self._surface.set_alpha(180)
        #     surface.blit(self._surface, (x, y), (0, 0, width, height))

        facing = state.player.facing
        sprite = self.sprite_obj.get_current_sprite(facing)
        surface.blit(
            sprite,
            (
                state.player.arm_x + x_off - (sprite.width if facing is Side.LEFT else 0),
                state.player.arm_y + y_off - sprite.height / 2,
            ),
        )
