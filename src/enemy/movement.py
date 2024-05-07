from math import isclose
from random import getrandbits, random, uniform

from hitbox import Hitbox
from map import Map
from util_types import Side, Direction
from wall import Wall


class EnemyMovement(Hitbox):

    # The chance of a non-moving enemy starting to move per tick
    MOVE_CHANCE: float = 0.01

    def __init__(self, current_map: Map, platform: Wall, x: float, y: float, width: int, height: int, speed: float):
        super().__init__(x, y, width, height)
        self.map = current_map
        self.platform: Wall = platform  # The platform this enemy is on
        self.speed: float = speed  # Movement speed (px/s)
        self.gravity: float = 0
        self.facing: Side = Side.RIGHT if getrandbits(1) else Side.LEFT  # Random init dir
        self.moving: bool = False
        self.move_target: float

    def tick(self, dt: float):
        if not self.moving:
            if random() < EnemyMovement.MOVE_CHANCE:
                self._start_move()
        else:
            self._tick_move(dt)

        self.gravity += Map.GRAVITY * dt
        collisions = self.move_axis(0, self.gravity * dt, self.map.walls)
        for direction, entity in collisions:
            if direction == Direction.DOWN and isinstance(entity, Wall):
                self.gravity = 0

    def _start_move(self):
        self.move_target = uniform(self.platform.left + self.width / 2, self.platform.right - self.width / 2)
        self.moving = True

    def _tick_move(self, dt: float):
        if isclose(self.x, self.move_target):
            self.moving = False
        else:
            diff = self.move_target - self.x
            self.facing = Side.LEFT if diff < 0 else Side.RIGHT
            self.move_axis(diff if abs(diff) < self.speed * dt else self.speed * self.facing.value * dt,
                           0, self.map.walls)
