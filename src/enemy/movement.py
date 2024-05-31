from random import getrandbits, random, uniform

from box import Hitbox
from map import Map, Wall
from util.type import Direction, Side


class EnemyMovement(Hitbox):
    # The chance of a non-moving enemy starting to move per tick
    MOVE_CHANCE: float = 0.01

    # The distance (pixels) between the enemy and it's move target to be considered as reached the target
    TARGET_THRESHOLD: float = 0.01

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
    ):
        # Default values
        if x is None:
            x = uniform(platform.left, platform.right - width)
        if y is None:
            y = platform.top - height
        if facing is None:
            facing = Side.RIGHT if getrandbits(1) else Side.LEFT  # Random init dir

        # Init
        super().__init__(x, y, width, height)
        self.map: Map = current_map
        self.platform: Wall = platform  # The platform this enemy is on
        self.speed: float = speed  # Movement speed (px/s)
        self.gravity: float = 0
        self.facing: Side = facing
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
            lambda o: isinstance(o, Wall) and o is not self.platform,
        )
        if not obstacles:
            return self.platform.left, self.platform.right

        def check_collisions() -> bool:
            for obs in obstacles:
                if self.detect_collision(obs):
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

    def tick(self, dt: float) -> None:
        """Updates this Enemy's position and has a chance to start idle movement if not currently moving.

        Parameters
        ----------
        dt : float
            The seconds between this tick and the last.
        """

        if not self.moving:
            if random() < EnemyMovement.MOVE_CHANCE:
                self._start_move()
        else:
            self._tick_move(dt)

        self.gravity += Map.GRAVITY * dt
        collisions = self.move_axis(0, self.gravity * dt, self.map.walls)
        for direction, entity in collisions:
            if direction is Direction.DOWN and isinstance(entity, Wall):
                self.gravity = 0

    def _start_move(self) -> None:
        """Starts idle movement by choosing a target to move to."""

        self.move_target = uniform(self.area[0], self.area[1] - self.width)
        self.moving = True

    def _tick_move(self, dt: float) -> None:
        """Stops movement if this Enemy has reached its target, otherwise moves it towards its target.

        Parameters
        ----------
        dt : float
            The seconds between this tick and the last.
        """

        if abs(self.x - self.move_target) < EnemyMovement.TARGET_THRESHOLD:
            self.moving = False
        else:
            diff = self.move_target - self.x
            self.facing = Side.LEFT if diff < 0 else Side.RIGHT
            self.move_axis(
                (diff if abs(diff) < self.speed * dt else self.speed * self.facing.value * dt),
                0,
                self.map.walls,
            )
