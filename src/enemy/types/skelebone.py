import math

from map import Map, Wall
from player import Player
from util.func import normalise_rect
from util.type import Rect, Side

from ..attack import DiagonalUpOut
from ..enemy import Enemy
from ..movement import GroundIdleMovement
from ..sprite import SPRITES_PER_SECOND

ATTACK_TIME: int = (1 / SPRITES_PER_SECOND) * 7
ATK_END_TIME: float = ATTACK_TIME * 3 / 7  # Time which is not attacking at the end of an attack anim


class Skelebone(Enemy, GroundIdleMovement, DiagonalUpOut):
    I_FRAMES: float = 0.3

    @property
    def current_atk_time(self) -> float:
        return (self.atk_time - ATK_END_TIME) / (self.atk_length - ATK_END_TIME)

    def __init__(self, player: Player, current_map: Map, platform: Wall):
        super().__init__(
            player,
            current_map,
            platform,
            size=(40, 74),
            mass=2,
            speed=100,
            sense_size=(500, 300),
            xray=False,
            atk_width=40,
            atk_height=60,
            atk_height_tick=8,
            arm_y=0.6,
            atk_windup=ATTACK_TIME * 3 / 7,
            atk_speed=1.4,
            atk_length=ATTACK_TIME * 4 / 7,
            health=80,
            damage=10,
            sprite="skelebone",
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
