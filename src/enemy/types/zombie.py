from map import Map, Wall
from player import Player
from util.type import Direction, Vec2

from ..attack import SwordAttack
from ..enemy import Enemy
from ..movement import GroundIdleMovement


class Zombie(Enemy, GroundIdleMovement, SwordAttack):
    def __init__(self, player: Player, current_map: Map, platform: Wall):
        super().__init__(
            player,
            current_map,
            platform,
            size=(20, 35),
            speed=100,
            sense_size=(500, 300),
            xray=False,
            atk_width=30,
            atk_windup=0.3,
            atk_speed=1.4,
            atk_length=0.2,
            health=800,
            damage=20,
            arm_y=0.2,
            atk_height=40,
            atk_height_tick=8,
        )

    def take_hit(self, damage: int, kb: Vec2 = None, direction: Direction = None, **kwargs):
        self.health -= damage
        print(f"Zombie hit: {self.health}")
        if kb is not None:
            if direction is not None:
                self.vx += kb[0] * direction.value
            self.vy += kb[1]
