from map import Map
from util_types import Side
from wall import Wall
from .movement import EnemyMovement


class Enemy:

    @property
    def x(self):
        return self.movement.x

    @x.setter
    def x(self, value):
        self.movement.x = value

    @property
    def y(self):
        return self.movement.y

    @y.setter
    def y(self, value):
        self.movement.y = value

    def __init__(self, current_map: Map, platform: Wall, width: int, height: int, speed: float,
                 x: float = None, y: float = None, facing: Side = None):
        self.movement: EnemyMovement = EnemyMovement(current_map, platform, width, height, speed, x, y, facing)

    def tick(self, dt: float):
        self.movement.tick(dt)
