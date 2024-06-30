from constants import SPRITES_PER_SECOND
from item.pickup import (
    DamagePotion,
    HealthPotion,
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


class Werewolf(Enemy, GroundIdleMovement, DiagonalUpOut):
    # High chance for toe, everything else same
    LOOT_POOL: list[Pickup] = [Toe, Toe, Sausages, DamagePotion, HealthPotion]

    I_FRAMES: float = 0.3

    @property
    def current_atk_time(self) -> float:
        return (self.atk_time) / (self.atk_length)

    def __init__(self, platform: Wall, colour: str):
        super().__init__(
            platform,
            size=(45, 80),
            mass=1.5,
            speed=100,
            sense_size=(600, 500),
            sense_anchor=(0.4, 0.5),
            xray=True,
            alert_delay=(1 / SPRITES_PER_SECOND) * 3,
            alert_retain_length=3,
            atk_width=40,
            atk_height=60,
            atk_height_tick=8,
            arm_y=0.6,
            atk_windup=(1 / SPRITES_PER_SECOND) * 4,
            atk_speed=0.8,
            atk_length=(1 / SPRITES_PER_SECOND) * 2,
            health=40,
            damage=15,
            sprite=f"werewolf/{colour}",
            loot_chance=0.18,
        )

    def _get_real_atk_area(self) -> Rect:
        return normalise_rect(
            self.front,
            self.atk_top + (self.atk_height - self.atk_height_tick) * self.current_atk_time,
            int(self.atk_width * (1 - self.current_atk_time**2)) * (1 if self.facing is Side.RIGHT else -1),
            self.atk_height_tick,
        )


class RedWerewolf(Werewolf):
    def __init__(self, platform: Wall):
        super().__init__(platform, "red")


class BlackWerewolf(Werewolf):
    def __init__(self, platform: Wall):
        super().__init__(platform, "black")


class WhiteWerewolf(Werewolf):
    def __init__(self, platform: Wall):
        super().__init__(platform, "white")
