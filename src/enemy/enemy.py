from map import Map, Wall
from util.type import Side

from .movement import EnemyMovement


class Enemy:
    @property
    def x(self):
        return self.movement.x

    @property
    def y(self):
        return self.movement.y

    @property
    def width(self):
        return self.movement.width

    @property
    def height(self):
        return self.movement.height

    @property
    def facing(self):
        return self.movement.facing

    @property
    def head_x(self):
        return self.x + self.width * (self._head_x if self.facing is Side.LEFT else 1 - self._head_x)

    @property
    def head_y(self):
        return self.y + self.height * self._head_y

    def __init__(
        self,
        current_map: Map,
        platform: Wall,
        width: int,
        height: int,
        speed: float,
        x: float = None,
        y: float = None,
        facing: Side = None,
        head_x: float = 0.5,  # Head position, see head_x property, 0 = facing, 1 = opposite
        head_y: float = 0.3,  # See head_y property, 0 = top, 1 = bottom
        head_angle: float = 0,  # The angle to the horizontal of the head facing (radians) (positive = down)
    ):
        self.movement: EnemyMovement = EnemyMovement(current_map, platform, width, height, speed, x, y, facing)

        self._head_x: float = head_x
        self._head_y: float = head_y

    def tick(self, dt: float):
        self.movement.tick(dt)
