from map import Map, Wall
from player import Player
from util.func import normalise_rect
from util.type import Rect, Side

from ..attack import SwordAttack
from ..enemy import Enemy
from ..movement import GroundIdleMovement
from ..sprite import SPRITES_PER_SECOND

ATTACK_TIME: int = (1 / SPRITES_PER_SECOND) * 7
REAL_ATK_LENGTH: float = ATTACK_TIME * 2 / 7


class Skelebone(Enemy, GroundIdleMovement, SwordAttack):
    I_FRAMES: float = 0.3

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
            atk_width=20,
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
        if self.atk_time > REAL_ATK_LENGTH:
            return normalise_rect(
                self.front,
                self.atk_top
                + (self.atk_height - self.atk_height_tick)
                * ((self.atk_time - REAL_ATK_LENGTH) / (self.atk_length - REAL_ATK_LENGTH)),
                self.atk_width * (1 if self.facing is Side.RIGHT else -1),
                self.atk_height_tick,
            )
        return 0, 0, 0, 0
