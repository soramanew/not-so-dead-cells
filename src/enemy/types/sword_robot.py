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


class SwordRobot(Enemy, GroundIdleMovement, DiagonalUpOut):
    # Low chance for sausage, everything else same
    LOOT_POOL: list[Pickup] = [
        Apple,
        Apple,
        Toe,
        Toe,
        LemonPie,
        LemonPie,
        Sausages,
        DamagePotion,
        DamagePotion,
        HealthPotion,
        HealthPotion,
    ]

    I_FRAMES: float = 0.3

    @property
    def current_atk_time(self) -> float:
        return (self.atk_time) / (self.atk_length)

    def __init__(self, platform: Wall):
        super().__init__(
            platform,
            size=(40, 74),
            mass=4,
            speed=100,
            sense_size=(600, 300),
            xray=True,
            alert_delay=(1 / SPRITES_PER_SECOND) * 5,
            alert_retain_length=5,
            atk_width=40,
            atk_height=60,
            atk_height_tick=8,
            arm_y=0.6,
            atk_windup=(1 / SPRITES_PER_SECOND),
            atk_speed=0.5,
            atk_length=(1 / SPRITES_PER_SECOND) * 3,
            health=100,
            damage=2,
            sprite="sword_robot",
            loot_chance=0.34,
        )

    def _get_real_atk_area(self) -> Rect:
        return normalise_rect(
            self.front,
            self.atk_top + (self.atk_height - self.atk_height_tick) * self.current_atk_time,
            int(self.atk_width * math.sin((1 - self.current_atk_time) * math.pi))
            * (1 if self.facing is Side.RIGHT else -1),
            self.atk_height_tick,
        )
