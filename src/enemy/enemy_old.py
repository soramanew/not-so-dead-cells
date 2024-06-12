import math

from map import Map, Wall
from util.type import Side

from .movement import EnemyMovement
from .sense import EnemySense


class Enemy:
    @property
    def x(self) -> float:
        return self.movement.x

    @property
    def y(self) -> float:
        return self.movement.y

    @property
    def width(self) -> int:
        return self.movement.width

    @property
    def height(self) -> int:
        return self.movement.height

    @property
    def facing(self) -> Side:
        return self.movement.facing

    @property
    def head_x(self) -> float:
        return self.x + self.width * (self._head_x if self.facing is Side.LEFT else 1 - self._head_x)

    @property
    def head_y(self) -> float:
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
        head_angle: float = math.pi / 2,  # The angle to the horizontal of the head facing (radians) (positive = down)
        sense_anchor_x: float = 0,  # The x anchor point of the sense in direction of facing, 0 = opposite, 1 = facing
        sense_anchor_y: float = 0.5,  # The y anchor point of the sense (see EnemySense#anchor_yr)
    ):
        self.movement: EnemyMovement = EnemyMovement(current_map, platform, width, height, speed, x, y, facing)

        self._head_x: float = head_x
        self._head_y: float = head_y

        self.sense: EnemySense = EnemySense(self, head_angle, 40, 20, sense_anchor_x, sense_anchor_y)

    def tick(self, dt: float):
        self.movement.tick(dt)
