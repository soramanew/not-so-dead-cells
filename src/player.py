import math

from hitbox import Hitbox
from map import Map
from utils import clamp


class Player(Hitbox):
    # The amount of vx the controls add per second (px/s/s)
    SIDE_SPEED_ACCEL: int = 1000
    # The max speed the player can move sideways when not rolling (px/s)
    SIDE_SPEED_CAP: int = 80
    # The max speed the player can move downwards when not slamming (px/s)
    DROP_SPEED_CAP: int = 400

    # The upwards vy added on jump
    JUMP_STRENGTH = 200
    # The vx added on roll in the facing direction
    ROLL_STRENGTH: int = 300
    # The downwards vy added on slam
    SLAM_STRENGTH: int = 800

    # The max number of jumps the player has
    JUMPS: int = 200

    # Roll cooldown in seconds
    ROLL_COOLDOWN: float = 0.3

    # The decay of the rolling velocity per second (roll for 1 second)
    ROLL_VX_DECAY: int = 1
    # The decay of the velocity added by controlling the player
    CONTROL_VX_DECAY: int = 10
    # The decay of the slamming velocity
    SLAM_VY_DECAY: int = 1

    # -------------------------- Static Methods -------------------------- #

    @staticmethod
    def roll_height_fn(x):
        return 4 * abs(x - 0.5) - 1

    # ---------------------------- Properties ---------------------------- #

    @property
    def vx(self):
        return self.controlled_vx + self.roll_vx

    @vx.setter
    def vx(self, value):
        total_vx = self.vx or 1  # So no division by 0
        self.controlled_vx = value * (self.controlled_vx / total_vx)
        self.roll_vx = value * (self.roll_vx / total_vx)
        # TODO: doesn't keep momentum on jump, find better way to do this

    @property
    def vy(self):
        return self.general_vy + self.slam_vy

    @vy.setter
    def vy(self, value):
        total_vy = self.vy or 1  # So no division by 0
        self.general_vy = value * (self.general_vy / total_vy)
        self.slam_vy = value * (self.slam_vy / total_vy)

    @property
    def rolling(self):
        return self._rolling

    @rolling.setter
    def rolling(self, value: bool):
        self._rolling = value
        # Add roll velocity on start rolling
        if value:
            # Cancel slam if slamming
            if self.slamming:
                self.slamming = False
            self.vx = 0
            self.roll_vx = Player.ROLL_STRENGTH * self.facing
        # Reset cooldown on stop rolling and move vx over to controlled
        else:
            self.roll_cooldown = Player.ROLL_COOLDOWN
            self.controlled_vx = self.roll_vx
            self.roll_vx = 0

    @property
    def roll_vx(self):
        return self._roll_vx

    @roll_vx.setter
    def roll_vx(self, value: float):
        self._roll_vx = value

        try:
            if self.rolling and value != 0 and abs(value) <= Player.SIDE_SPEED_CAP:
                self.rolling = False
        except AttributeError:
            # Ignore self.rolling attribute error on initialisation
            pass

    @property
    def slamming(self):
        return self._slamming

    @slamming.setter
    def slamming(self, value):
        self._slamming = value
        # Add slam velocity on start slamming
        if value:
            # Cancel roll if rolling
            if self.rolling:
                self.rolling = False
            self.general_vy = 0
            self.slam_vy = Player.SLAM_STRENGTH
        # Reduce slam velocity on stop slamming
        else:
            self.general_vy = self.slam_vy
            self.slam_vy = 0

    @property
    def slam_vy(self):
        return self._slam_vy

    @slam_vy.setter
    def slam_vy(self, value: float):
        self._slam_vy = value

        try:
            if self.slamming and value != 0 and value < Player.DROP_SPEED_CAP:
                self.slamming = False
        except AttributeError:
            # Ignore self.slamming attribute error during initialisation
            pass

    # ---------------------------- Constructor ---------------------------- #

    def __init__(self, x: float, y: float, width: int = 10, height: int = 30):
        super().__init__(x, y, width, height)
        self.jumps = Player.JUMPS  # How many jumps the player has left (is reset when touching ground)
        self.roll_vx = 0  # The velocity added by rolling
        self.rolling = False  # If the player is currently rolling
        self.roll_cooldown = 0  # The time until the player can roll again in seconds
        self.facing = 1  # The direction the player is currently facing (-1 for left, 1 for right)
        self.controlled_vx = 0  # The controlled velocity of the player in the x direction (- is left, + is right)
        self.general_vy = 0  # The general (not slamming) velocity in the y direction (- is up, + is down)
        self.slam_vy = 0  # The velocity added by slamming
        self.slamming = False  # If the player is currently slamming
        self.base_height = height
        self.min_roll_height = height // 3

    # ------------------------------ Methods ------------------------------ #

    def handle_moves(self, dt, *move_types):
        """Handles movement commands.

        Parameters
        ----------
        dt : float
            The number of seconds between this tick and the last tick.
        *move_types : str
            The commands to do. Can be 'left', 'right', 'jump', 'roll' or 'slam'.

        See Also
        --------
        move_left(), move_right()
        jump()
        rolling
        slamming
        """

        if not self.rolling and "left" in move_types:
            self.move_left(dt)

        if not self.rolling and "right" in move_types:
            self.move_right(dt)

        # NOTE: order matters for the below moves as they will override each other

        # Cannot jump if currently slamming or no jumps left
        if not self.slamming and self.jumps > 0 and "jump" in move_types:
            self.jump()

        # Cannot roll if currently rolling or roll is on cooldown
        if not self.rolling and self.roll_cooldown <= 0 and "roll" in move_types:
            self.rolling = True

        if not self.slamming and "slam" in move_types:
            self.slamming = True

    def move_left(self, dt):
        """Adds velocity in the left direction and changes facing directions.

        Parameters
        ----------
        dt : float
            The number of seconds between this tick and the last tick.
        """
        # If facing opposite direction, accelerate in direction (left)
        if self.facing > 0:
            self.controlled_vx -= Player.SIDE_SPEED_ACCEL * dt
        # If less than speed cap, accelerate but cap at speed cap
        elif abs(self.controlled_vx) < Player.SIDE_SPEED_CAP:
            self.controlled_vx -= Player.SIDE_SPEED_ACCEL * dt
            if abs(self.controlled_vx) > Player.SIDE_SPEED_CAP:
                self.controlled_vx = -Player.SIDE_SPEED_CAP
        # Change direction facing
        self.facing = -1

    def move_right(self, dt):
        """Adds velocity in the right direction and changes facing direction.

        Parameters
        ----------
        dt : float
            The number of seconds between this tick and the last tick.
        """
        # If facing opposite direction, accelerate in direction (right)
        if self.facing < 0:
            self.controlled_vx += Player.SIDE_SPEED_ACCEL * dt
        # If less than speed cap, accelerate but cap at speed cap
        elif abs(self.controlled_vx) < Player.SIDE_SPEED_CAP:
            self.controlled_vx += Player.SIDE_SPEED_ACCEL * dt
            if abs(self.controlled_vx) > Player.SIDE_SPEED_CAP:
                self.controlled_vx = Player.SIDE_SPEED_CAP
        # Change direction facing
        self.facing = 1

    def jump(self):
        """Jump... Cancel rolling + decrement jump + add jump velocity."""
        # Cancel roll if rolling
        if self.rolling:
            self.rolling = False
        self.jumps -= 1
        # Set total vy to negative jump strength
        self.vy = 0
        self.general_vy = -Player.JUMP_STRENGTH

    def update_position(self, dt, boxes):
        """Updates the position of the player by the velocities * dt.

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds.
        boxes : list of Hitbox
            A list of Hitboxes to check for collisions with.
        """

        collisions = self.move(self.vx * dt, self.vy * dt, boxes)

        if "bottom" in collisions:
            self.jumps = Player.JUMPS
            self.slamming = False
            self.vy = 0
            self.vx /= 1 + Map.FRICTION

        # TODO: climb ledges, wall climbing

    def tick_changes(self, dt):
        """Updates the values which change per tick.

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds
        """

        # Decay velocities
        self.controlled_vx /= 1 + Player.CONTROL_VX_DECAY * dt
        self.slam_vy /= 1 + Player.SLAM_VY_DECAY * dt

        # Apply gravity if not slamming
        if not self.slamming:
            self.general_vy += Map.GRAVITY * dt
            if self.general_vy > Player.DROP_SPEED_CAP:
                self.general_vy = Player.DROP_SPEED_CAP

        # Tick roll cooldown
        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt

        # Change height while rolling
        if self.rolling:
            self.roll_vx -= math.copysign(Player.ROLL_STRENGTH * Player.ROLL_VX_DECAY * dt, self.roll_vx)
            roll_height = clamp(int(self.base_height * Player.roll_height_fn(
                abs(self.roll_vx) / Player.ROLL_STRENGTH)), self.base_height, self.min_roll_height)
            self.top += self.height - roll_height
            self.height = roll_height
        elif self.height != self.base_height:
            # If not rolling and height is not base_height (e.g. when rolling is interrupted via jumping),
            # transition height to base height
            diff = self.base_height - self.height
            # If gap is small just snap it to base_height (if not it will never reach base_height)
            if diff < self.base_height / 10:
                self.top -= diff
                self.height = self.base_height
            # Otherwise transition it
            else:
                diff //= 3
                self.top -= diff
                self.height += diff
