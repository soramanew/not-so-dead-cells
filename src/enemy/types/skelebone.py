import math

from constants import SPRITES_PER_SECOND
from item.pickup import (
    Apple,
    DamagePotion,
    HealthPotion,
    LemonPie,
    Pickup,
    Sausages,
    Toe,
)
from map import Wall
from util.func import normalise_rect
from util.type import Rect, Side

from ..attack import DiagonalUpOut
from ..enemy import Enemy
from ..movement import GroundIdleMovement

SPRITE_LENGTH: int = 1 / SPRITES_PER_SECOND
ATK_END_TIME: float = SPRITE_LENGTH * 3  # Time which is not attacking at the end of an attack anim


class Skelebone(Enemy, GroundIdleMovement, DiagonalUpOut):
    # High chance for toe, then health potion, apple & lemon pie, then sausage & damage pot lowest
    LOOT_POOL: list[Pickup] = [
        Apple,
        Apple,
        Toe,
        Toe,
        Toe,
        LemonPie,
        LemonPie,
        Sausages,
        DamagePotion,
        HealthPotion,
        HealthPotion,
    ]

    @property
    def current_atk_time(self) -> float:
        return (self.atk_time - ATK_END_TIME) / (self.atk_length - ATK_END_TIME)

    def __init__(self, platform: Wall):
        super().__init__(
            platform,
            size=(40, 74),
            mass=2,
            speed=100,
            sense_size=(500, 300),
            xray=False,
            alert_delay=SPRITE_LENGTH * 3,
            alert_retain_length=7.5,
            atk_width=40,
            atk_height=60,
            atk_height_tick=8,
            arm_y=0.6,
            atk_windup=SPRITE_LENGTH * 3,
            atk_speed=1.4,
            atk_length=SPRITE_LENGTH * 4,
            health=80,
            damage=10,
            sprite="skelebone",
            loot_chance=0.24,
            stagger_length=SPRITE_LENGTH * 3,
        )

    def _get_real_atk_area(self) -> Rect:
        if self.atk_time > ATK_END_TIME:
            return normalise_rect(
                self.front,
                self.atk_top + (self.atk_height - self.atk_height_tick) * self.current_atk_time,
                int(self.atk_width * math.sin((1 - self.current_atk_time) * math.pi))
                * (1 if self.facing is Side.RIGHT else -1),
                self.atk_height_tick,
            )
        return 0, 0, 0, 0
