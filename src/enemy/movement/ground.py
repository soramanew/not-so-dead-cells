import logging
from math import copysign
from random import random, uniform

import state
from map import Map, Wall
from util.func import clamp
from util.type import Direction, EnemyState, Side

from ..enemyabc import EnemyABC

logger = logging.getLogger(__name__)


class GroundMovement(EnemyABC):
    """Enemy movement along a platform."""

    # The distance (pixels) between the enemy and it's move target to be considered as reached the target
    TARGET_THRESHOLD: float = 0.01
    # Speed percent when idle
    IDLE_SPEED: float = 0.8

    @property
    def moving(self) -> bool:
        return self._moving

    @moving.setter
    def moving(self, value: bool) -> None:
        # Can only move when on platform
        self._moving = value and self.on_platform

    @property
    def speed(self) -> float:
        return self._speed * (1 if self.can_sense_player else self.IDLE_SPEED)

    def __init__(self, speed: float, **kwargs):
        super().__init__(**kwargs)
        self._speed: float = speed  # Movement speed (px/s)
        self.on_platform: bool = False
        self.moving: bool = False
        self.move_target: float = None
        self.vx: float = 0  # x velocity due to knockback
        self.vy: float = 0
        self.area: tuple[float, float] = self._get_area()

    def _get_area(self) -> tuple[float, float]:
        """Finds the area which this Enemy can move on it's platform without colliding with obstacles above it.

        This method will move the enemy spawn if it is colliding with an obstacle.

        Returns
        -------
        tuple of float, float
            The x bounds in which this enemy can move.
        """

        logger.debug("Getting area...")

        obstacles = state.current_map.get_rect(
            self.platform.x,
            self.platform.y - self.height,
            self.platform.width,
            self.height,
            lambda o: o is not self.platform and isinstance(o, Wall),
        )
        if not obstacles:
            logger.debug("No obstacles")
            return self.platform.left, self.platform.right

        def check_collisions() -> bool:
            for obs in obstacles:
                if self.detect_collision_box(obs):
                    return True
            return False

        moves = 0
        max_moves = 500
        while moves < max_moves and check_collisions():
            self.x = uniform(
                self.platform.left,
                self.platform.right - self.width,
            )
            moves += 1

        if moves < max_moves:
            logger.debug(f"Moved {moves} times")
        else:
            logger.warn("Max moves reached. Ignoring.")
            return 0, 0

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

    def _tick_move(self, dt: float) -> None:
        """Updates this Enemy's position and has a chance to start idle movement if not currently moving.

        Parameters
        ----------
        dt : float
            The seconds between this tick and the last.
        """

        force = (
            Map.get_air_resistance(self.vx, self.height)
            + (copysign(Map.GRAVITY * self.mass * Wall.FRICTION, self.vx) if self.on_platform else 0)
        ) * dt
        if abs(force) > abs(self.vx):
            force = self.vx
        self.vx -= force
        self.vy += (Map.GRAVITY - Map.get_air_resistance(self.vy, self.width)) * dt

        self.on_platform = False
        collisions = self.move(self.vx * dt, self.vy * dt)
        for direction, entity in collisions:
            if direction is Direction.DOWN and isinstance(entity, Wall):
                self.vy = 0
                self.on_platform = True
                if entity is not self.platform:
                    self.platform = entity
                    self.area = self._get_area()
                    self.moving = False
                    logger.debug(f"Enemy changed platform: {entity} | Area: {self.area}")

        if self.can_sense_player:
            self.move_target = clamp(
                state.player.x
                - min(
                    (self if self.facing is Side.RIGHT else state.player).width + self.atk_width * 0.8,
                    abs(state.player.x - self.x),
                )
                * self.facing.value,
                self.area[1] - self.width,
                self.area[0],
            )
            self.moving = True

        if self.attacking or self.alerting or self.staggered:
            return

        if self.moving:
            # Tick movement
            if abs(self.x - self.move_target) < GroundMovement.TARGET_THRESHOLD:
                self.moving = False
            else:
                diff = self.move_target - self.x
                self.facing = Side.LEFT if diff < 0 else Side.RIGHT
                speed = self.speed * dt
                # If vx not same direction as facing, reduce it by speed
                if self.vx * self.facing.value < 0:
                    self.vx -= copysign(min(speed, abs(self.vx)), self.vx)
                self.move((diff if abs(diff) < speed else speed * self.facing.value), 0)

        if self.moving:
            self.state = EnemyState.SPRINTING if self.can_sense_player else EnemyState.WALKING
        else:
            self.state = EnemyState.IDLE


class GroundIdleMovement(GroundMovement):
    """Ground movement with idle movement."""

    # The chance of a non-moving enemy starting to move per tick
    MOVE_CHANCE: float = 0.005

    def _tick_move(self, dt: float) -> None:
        super()._tick_move(dt)

        if not self.moving:
            if random() < self.MOVE_CHANCE:  # self so can override
                # Start moving
                self.move_target = uniform(self.area[0], self.area[1] - self.width)
                self.moving = True
