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

ATTACK_TIME: int = (1 / SPRITES_PER_SECOND) * 6
ATK_END_TIME: float = ATTACK_TIME * 3 / 6  # Time which is not attacking at the end of an attack anim


class Plent(Enemy, GroundIdleMovement, DiagonalUpOut):
    # High chance for damage potion, then apple then rest equal
    LOOT_POOL: list[Pickup] = [
        Apple,
        Apple,
        Toe,
        LemonPie,
        Sausages,
        DamagePotion,
        DamagePotion,
        DamagePotion,
        HealthPotion,
    ]

    I_FRAMES: float = 0.3
    MOVE_CHANCE: float = 0.003

    @property
    def current_atk_time(self) -> float:
        return (self.atk_time - ATK_END_TIME) / (self.atk_length - ATK_END_TIME)

    def __init__(self, platform: Wall):
        super().__init__(
            platform,
            size=(40, 50),
            head_pos=(0.6, 0.6),
            mass=1.4,
            speed=70,
            sense_size=(400, 400),
            sense_anchor=(0.4, 0.6),
            xray=False,
            alert_delay=(1 / SPRITES_PER_SECOND) * 4,
            alert_retain_length=10,
            atk_width=45,
            atk_height=60,
            atk_height_tick=15,
            arm_y=0.5,
            atk_windup=ATTACK_TIME * 2 / 6,
            atk_speed=2,
            atk_length=ATTACK_TIME * 4 / 6,
            health=50,
            damage=20,
            sprite="plent",
            loot_chance=0.2,
        )

    def _get_real_atk_area(self) -> Rect:
        if self.atk_time > ATK_END_TIME:
            return normalise_rect(
                self.front,
                self.atk_top + (self.atk_height - self.atk_height_tick) * self.current_atk_time,
                int(self.atk_width * (1 - self.current_atk_time**2)) * (1 if self.facing is Side.RIGHT else -1),
                self.atk_height_tick,
            )
        return 0, 0, 0, 0
