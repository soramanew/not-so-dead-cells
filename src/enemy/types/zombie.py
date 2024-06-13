from map import Map, Wall
from player import Player

from ..attack import SwordAttack
from ..enemy import Enemy


class Zombie(Enemy, SwordAttack):
    def __init__(self, player: Player, current_map: Map, platform: Wall):
        super().__init__(
            player,
            current_map,
            platform,
            size=(20, 35),
            speed=100,
            sense_size=(500, 300),
            atk_width=30,
            atk_windup=0.4,
            atk_speed=3,
            atk_length=0.2,
            health=800,
            damage=20,
            arm_y=0.2,
            atk_height=40,
            atk_height_tick=8,
        )
