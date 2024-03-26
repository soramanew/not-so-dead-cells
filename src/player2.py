import pygame.key

import key_handler
from wall import Wall
from hitbox import Hitbox
from map import Map
from util_types import Direction, Collision, run_once, PlayerControl, Side
from utils import clamp


class Player(Hitbox):
    # The amount of vx the controls add per second (px/s/s)
    CONTROL_ACCEL: int = 1000
    # The decay/s of the speed added by controlling the player
    CONTROL_SPEED_DECAY: int = 7

    # The max number of jumps the player has
    JUMPS: int = 2
    # The upwards velocity added on jump
    JUMP_STRENGTH: int = 300
    # The side velocity added on wall jumping
    WALL_JUMP_STRENGTH: float = 300

    # The speed of rolling (px/s)
    ROLL_SPEED: int = 300
    # The length of a roll (s)
    ROLL_LENGTH: float = 0.5
    # The time until the player can roll again after a roll is finished (s)
    ROLL_COOLDOWN: float = 0.3

    # The max speed the player can move downwards when not slamming (px/s)
    DROP_SPEED_CAP: int = 800
    # The downwards velocity added on slam
    SLAM_STRENGTH: int = 1200

    # A multiplier to the wall sliding vy decay
    GRAB_STRENGTH: int = 60

    # -------------------------- Static Methods -------------------------- #

    @staticmethod
    def roll_height_fn(x):
        return 4 * abs(x - 0.5) - 1

    # ---------------------------- Constructor ---------------------------- #

    def __init__(self, current_map: Map, x: float, y: float, width: int = 10, height: int = 30):
        super().__init__(x, y, width, height)
        self.current_map: Map = current_map
        self.vx: float = 0  # The velocity of the player in the x direction (- left, + right)
        self.vy: float = 0  # The velocity of the player in the y direction (- up, + down)
        self.controlled_vx: float = 0  # The velocity of the player in the x direction caused by user controls
        self.facing: Side = Side.RIGHT  # The direction the player is currently facing (-1 for left, 1 for right)
        self.jumps: int = Player.JUMPS  # How many jumps the player has left (is reset when touching ground)
        self.roll_cooldown: float = 0  # The time until the player can roll again in seconds
        self.slamming: bool = False  # If the player is currently slamming
        self.base_height: int = height
        self.min_roll_height: int = height // 3
        self.on_platform: bool = False
        self.roll_time: float = 0
        self.wall_sliding_dir: Side | None = None
        self.ledge_climbing: bool = False

    # ------------------------------ Getters ------------------------------ #

    def is_rolling(self) -> bool:
        return self.roll_time > 0

    def can_jump(self) -> bool:
        return not self.slamming and (self.jumps > 0 or self.wall_sliding_dir)

    # ------------------------------ Methods ------------------------------ #

    def handle_moves(self, dt: float, *move_types: PlayerControl) -> None:
        """Handles movement commands.

        See Also
        --------
        _x_control()
        _jump()
        _roll()
        _slam()

        Parameters
        ----------
        dt : float
            The number of seconds between this tick and the last tick.
        *move_types : PlayerControl
            The moves to perform.
        """

        if not self.is_rolling() and PlayerControl.LEFT in move_types:
            self._x_control(Side.LEFT, dt)

        if not self.is_rolling() and PlayerControl.RIGHT in move_types:
            self._x_control(Side.RIGHT, dt)

        # NOTE: order matters for the below moves as they will override each other

        # Cannot jump if currently slamming or no jumps left
        if self.can_jump() and PlayerControl.JUMP in move_types:
            self._jump()

        # Cannot roll if currently rolling or roll is on cooldown
        if not self.is_rolling() and self.roll_cooldown <= 0 and PlayerControl.ROLL in move_types:
            self._roll()

        if not self.slamming and PlayerControl.SLAM in move_types:
            self._slam()

    def _x_control(self, direction: Side, dt: float) -> None:
        """Adds velocity (accelerates) in the x direction and changes facing direction.

        Parameters
        ----------
        direction : Side
            The direction of the acceleration.
        dt : float
            The number of seconds between this tick and the last tick.
        """

        # Apply acceleration
        self.controlled_vx += Player.CONTROL_ACCEL * dt * direction.value
        # Change direction facing
        self.facing = direction

    def _jump(self) -> None:
        """Jump... Cancel rolling + decrement jump + add jump velocity."""

        # Cancel roll if rolling
        if self.is_rolling():
            stopped_rolling = self._stop_rolling()
            if not stopped_rolling:
                return

        # Set vy to negative jump strength
        self.vy = -Player.JUMP_STRENGTH
        if self.wall_sliding_dir:
            # Set vx to opposing the wall to jump off
            self.controlled_vx = Player.WALL_JUMP_STRENGTH * -self.wall_sliding_dir.value
        else:
            # Do not consume a jump if wall jump
            self.jumps -= 1

    def _roll(self) -> None:
        """Cancel slam + roll"""
        if self.slamming:
            self.slamming = False
        self.roll_time = Player.ROLL_LENGTH

    def _stop_rolling(self) -> bool:
        """Stops the player from rolling if the player is able to stop rolling.

        Returns
        -------
        bool
            Whether the player stopped rolling or not.
        """

        walls_above = self.current_map.get_rect(self.x, self.y + self.height - self.base_height,
                                                self.width, self.base_height)
        for wall in walls_above:
            if (wall.top < self.top + self.height - self.base_height < wall.bottom and
                    wall.left < self.right and wall.right > self.left):
                # Top when at base height inside wall and x inside wall
                return False

        self.roll_time = -1
        self.roll_cooldown = Player.ROLL_COOLDOWN
        return True

    def _slam(self) -> None:
        """Cancel roll + slam"""
        if self.is_rolling():
            stopped_rolling = self._stop_rolling()
            if not stopped_rolling:
                return
        self.vy = Player.SLAM_STRENGTH
        self.slamming = True

    def update_position(self, dt: float) -> list[Collision]:
        """Updates the position of the player by the velocity * dt.

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds.

        Returns
        -------
        list of Collision
            A list of collisions with the player which happened due to this movement.
        """

        return self.move(self.vx * dt, self.vy * dt, self.current_map.walls)

    def handle_collisions(self, collisions: list[Collision]) -> None:
        """Handles player actions on collisions.

        Parameters
        ----------
        collisions : list of Direction
            The collisions the player experienced in this tick.
        """

        self._reset_collision_attrs()

        down_wall = run_once(self._handle_down_wall_collision)
        side_wall = run_once(self._handle_side_wall_collision)
        for direction, entity in collisions:
            if direction == Direction.DOWN and isinstance(entity, Wall):
                down_wall()
            if (direction == Direction.RIGHT or direction == Direction.LEFT) and isinstance(entity, Wall):
                side_wall(direction, entity)

        # TODO: climb ledges, wall climbing

    def _reset_collision_attrs(self) -> None:
        """Resets the attributes affected by methods called by handle_collision() to their default values.

        See Also
        --------
        _handle_down_wall_collision()
        _handle_side_wall_collision()
        """

        self.on_platform = False
        self.wall_sliding_dir = None

    def _handle_down_wall_collision(self) -> None:
        """Actions on downwards wall collisions.

        This should be called from handle_collisions() and wrapped with run_once().
        """

        self.on_platform = True
        self.jumps = Player.JUMPS
        self.slamming = False
        self.vy = 0

    def _handle_side_wall_collision(self, direction: Direction, wall: Wall) -> None:
        if ((key_handler.get(pygame.K_a) or key_handler.get(pygame.K_d)
             or key_handler.get(pygame.K_LEFT) or key_handler.get(pygame.K_RIGHT))
                and not self.is_rolling()):
            self.wall_sliding_dir = direction.value
            self.slamming = False
        # TODO: handle wall climbing
        # TODO: handle ledge climbing if close enough

    def tick_changes(self, dt: float) -> None:
        """Updates values every tick.

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds
        """

        # Apply air resistance and friction
        self.controlled_vx /= 1 + Player.CONTROL_SPEED_DECAY * dt
        self.vx /= 1 + (Map.AIR_RESISTANCE + (Wall.FRICTION if self.on_platform else 0)) * dt
        self.vy /= 1 + Map.AIR_RESISTANCE * dt
        if self.wall_sliding_dir:
            self.vy /= 1 + Wall.FRICTION * Player.GRAB_STRENGTH * dt

        self._tick_roll(dt)

        if not self.slamming:
            # Apply gravity and cap at speed cap
            self.vy += Map.GRAVITY * dt
            if self.vy > Player.DROP_SPEED_CAP:
                self.vy = Player.DROP_SPEED_CAP
        elif self.vy <= Player.DROP_SPEED_CAP:
            # Stop slamming if below speed cap
            self.slamming = False

    def _tick_roll(self, dt: float) -> None:
        """Updates roll-related properties.

        This method also syncs vx and controlled_vx.

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds
        """

        # Reduce roll cooldown
        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt

        if self.is_rolling():
            # Reduce roll time and set vx to roll speed if rolling
            self.roll_time -= dt
            self.vx = Player.ROLL_SPEED * self.facing.value
            if not self.is_rolling():
                self._stop_rolling()
        else:
            # Otherwise set total vx to controlled vx
            self.vx = self.controlled_vx

        # Sync controlled vx with total vx so rolling can transition seamlessly
        self.controlled_vx = self.vx

        self._change_roll_height(dt)

    def _change_roll_height(self, dt: float) -> None:
        """Changes the height of the player based on its progression through a roll.

        This method also changes the height of the player back to the base height if it is not rolling and
        extends the roll if the player is not able to exit rolling (blocked by wall above).

        Parameters
        ----------
        dt : float
            The time between this tick and the last.
        """

        walls_above = self.current_map.get_rect(self.x, self.y + self.height - self.base_height,
                                                self.width, self.base_height)
        if self.is_rolling():
            roll_height = clamp(int(self.base_height * Player.roll_height_fn(
                self.roll_time / Player.ROLL_LENGTH)), self.base_height, self.min_roll_height)

            do_change = True
            if roll_height > self.height:
                for wall in walls_above:
                    if (wall.top < self.top + self.height - self.base_height < wall.bottom and
                            wall.left < self.right and wall.right > self.left):
                        # Top when at base height inside wall and x inside wall
                        do_change = False

            if do_change:
                self.top += self.height - roll_height
                self.height = roll_height
            else:
                self.roll_time += dt
        elif self.height != self.base_height:
            # If not rolling and height is not base_height (e.g. when rolling is interrupted via jumping),
            # transition height to base height
            diff = self.base_height - self.height
            # If gap is small just snap it to base_height (if not it will never reach base_height)
            if diff < self.base_height / 10:
                new_top = self.top - diff
                new_height = self.base_height
            # Otherwise transition it
            else:
                diff //= 3
                new_top = self.top - diff
                new_height = self.height + diff

            do_change = True
            if new_height > self.height:
                for wall in walls_above:
                    if wall.top < new_top < wall.bottom and wall.left < self.right and wall.right > self.left:
                        # New top inside wall and x inside wall
                        do_change = False

            if do_change:
                self.top = new_top
                self.height = new_height
            else:
                self.roll_time += dt
