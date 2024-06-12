from random import random, uniform

from map import Wall
from player import Player
from util.func import clamp
from util.type import Side

from .enemyabc import EnemyABC


class Movement(EnemyABC):
    # The chance of a non-moving enemy starting to move per tick
    MOVE_CHANCE: float = 0.01

    # The distance (pixels) between the enemy and it's move target to be considered as reached the target
    TARGET_THRESHOLD: float = 0.01

    def __init__(self, speed: float, facing: Side = None, **kwargs):
        super().__init__(**kwargs)
        self.speed: float = speed  # Movement speed (px/s)
        self.moving: bool = False
        self.move_target: float
        self.area: tuple[float, float] = self._get_area()

    def _get_area(self) -> tuple[float, float]:
        """Finds the area which this Enemy can move on it's platform without colliding with obstacles above it.

        This method will move the enemy spawn if it is colliding with an obstacle.

        Returns
        -------
        tuple of float, float
            The x bounds in which this enemy can move.
        """

        obstacles = self.map.get_rect(
            self.platform.x,
            self.platform.y - self.height,
            self.platform.width,
            self.height,
            lambda o: o is not self.platform and isinstance(o, Wall),
        )
        if not obstacles:
            return self.platform.left, self.platform.right

        def check_collisions() -> bool:
            for obs in obstacles:
                if self.detect_collision_box(obs):
                    return True
            return False

        while check_collisions():
            self.x = uniform(
                self.platform.left,
                self.platform.right - self.width,
            )
            print("[DEBUG] Enemy spawn colliding: moving spawn")

        nearest_left = None
        nearest_right = None
        for wall in obstacles:
            diff = self.left - wall.right
            if diff >= 0 and (nearest_left is None or diff < nearest_left[0]):
                nearest_left = diff, wall.right
            diff = wall.left - self.right
            if diff >= 0 and (nearest_right is None or diff < nearest_right[0]):
                nearest_right = diff, wall.left

        return (
            (self.platform.left if nearest_left is None or nearest_left[1] < self.platform.left else nearest_left[1]),
            (
                self.platform.right
                if nearest_right is None or nearest_right[1] > self.platform.right
                else nearest_right[1]
            ),
        )

    def _tick_move(self, dt: float, player: Player) -> None:
        """Updates this Enemy's position and has a chance to start idle movement if not currently moving.

        Parameters
        ----------
        dt : float
            The seconds between this tick and the last.
        player : Player
            The player.
        """

        if self.alerted:
            self.move_target = clamp(
                player.x - min(self.width + self.atk_range, abs(player.x - self.x)) * self.facing.value,
                self.area[1],
                self.area[0],
            )
            self.moving = True

        if not self.moving:
            if random() < Movement.MOVE_CHANCE:
                # Start moving
                self.move_target = uniform(self.area[0], self.area[1] - self.width)
                self.moving = True
        else:
            # Tick movement
            if abs(self.x - self.move_target) < Movement.TARGET_THRESHOLD:
                self.moving = False
            else:
                diff = self.move_target - self.x
                self.facing = Side.LEFT if diff < 0 else Side.RIGHT
                self.move_axis(
                    (diff if abs(diff) < self.speed * dt else self.speed * self.facing.value * dt),
                    0,
                    self.map.walls,
                )
