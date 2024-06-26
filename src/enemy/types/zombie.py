from map import Map, Wall
from player import Player

from ..attack import SwordAttack
from ..enemy import Enemy
from ..movement import GroundIdleMovement


class Zombie(Enemy, GroundIdleMovement, SwordAttack):
    I_FRAMES: float = 0.3

    def __init__(self, player: Player, current_map: Map, platform: Wall):
        super().__init__(
            player,
            current_map,
            platform,
            size=(20, 35),
            mass=2,
            speed=100,
            sense_size=(500, 300),
            xray=False,
            atk_width=30,
            atk_windup=0.3,
            atk_speed=1.4,
            atk_length=0.2,
            health=80,
            damage=10,
            arm_y=0.2,
            atk_height=40,
            atk_height_tick=8,
        )
