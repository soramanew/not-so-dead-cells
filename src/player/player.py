import logging
from math import sqrt

import pygame
import state
from box import Hitbox
from item import Weapon
from item.pickup import WeaponPickup
from map import Gate, Map, Platform, Wall
from util import key_handler
from util.decor import run_once
from util.event import (
    PLAYER_DAMAGE_HEALTH_CHANGED,
    PLAYER_DAMAGE_MULTIPLIER_CHANGED,
    PLAYER_HEALTH_CHANGED,
    PLAYER_HEALTH_MULTIPLIER_CHANGED,
    PLAYER_HIT,
    PLAYER_MAX_HEALTH_CHANGED,
    PLAYER_MULTIPLIERS_CHANGED,
    PLAYER_WEAPON_CHANGED,
)
from util.func import clamp, get_project_root
from util.type import (
    Collision,
    Direction,
    Interactable,
    PlayerControl,
    PlayerState,
    Rect,
    Side,
    Size,
    Sound,
    Vec2,
)

from .sprite import EffectSprite, PlayerSprite

logger = logging.getLogger(__name__)


def _roll_height_fn(x):
    return 3 * abs(x - 0.5) - 0.5


class Player(Hitbox):
    # The amount of vx the controls add per second (px/s/s)
    CONTROL_ACCEL: int = 1000
    # The decay/s of the speed added by controlling the player
    CONTROL_SPEED_DECAY: int = 5
    # The amount sprinting affects the control decay (i.e. speed /= 1 + (control decay / sprint mul) * dt)
    SPRINT_MULTIPLIER: float = 1.2

    # The max number of jumps the player has
    JUMPS: int = 2
    # The upwards velocity added on jump
    JUMP_STRENGTH: int = 400
    # The side velocity added on wall jumping
    WALL_JUMP_STRENGTH: float = 300

    # The speed of rolling (px/s)
    ROLL_SPEED: int = 500
    # The length of a roll (s)
    ROLL_LENGTH: float = 0.3
    # The time until the player can roll again after a roll is finished (s)
    ROLL_COOLDOWN: float = 0.3

    # The max speed the player can move downwards when not slamming (px/s)
    DROP_SPEED_CAP: int = 500

    # The downwards velocity added on slam
    SLAM_STRENGTH: int = 1200
    # The damage range of slamming
    SLAM_RANGE: Size = 40, 5
    # The base damage of the slam
    SLAM_DAMAGE: int = 0.03
    # The base knockback of the slam
    SLAM_KB: Vec2 = 0.1, -0.16

    # A multiplier to the wall sliding vy decay
    GRAB_STRENGTH: int = 60

    # The number of seconds the player can wall climb for
    WALL_CLIMB_LENGTH: float = 0.5
    # The speed of wall climbing
    WALL_CLIMB_STRENGTH: int = 200

    # The height from the top of the player to the top of the platform that the player can climb up
    LEDGE_CLIMB_HEIGHT: float = 0.5
    # The speed at which the player can climb ledges (multiplier to player height)
    LEDGE_CLIMB_SPEED: float = 3

    # Invincibility frames after taking damage in seconds
    I_FRAMES: float = 0.3
    # The max health of the player
    MAX_HEALTH: float = 100
    # The decay of the health able to be regained after taking damage
    DAMAGE_HEALTH_DECAY: float = 0.7
    # Size
    WIDTH: int = 40
    HEIGHT: int = 64
    MIN_HEIGHT: int = 30

    # Range around the player that it can interact with objects
    INTERACT_RANGE: float = 10

    # For enemy soft collision
    G: int = 8000
    ε: float = 0.1
    REPULSION_CAP: int = 200

    @property
    def health(self) -> int:
        return self._health

    @health.setter
    def health(self, value: int) -> None:
        if self._health == value:
            return

        pygame.event.post(pygame.Event(PLAYER_HEALTH_CHANGED, amount=value - self._health, new_value=value))
        if value < self._health:
            self.i_frames = Player.I_FRAMES
        self._health = value

    @property
    def max_health(self) -> int:
        return self._max_health

    @max_health.setter
    def max_health(self, value: int) -> None:
        if self._max_health == value:
            return

        pygame.event.post(pygame.Event(PLAYER_MAX_HEALTH_CHANGED, amount=value - self._max_health, new_value=value))
        self._max_health = value

    @property
    def damage_health(self) -> int:
        return self._damage_health

    @damage_health.setter
    def damage_health(self, value: int) -> None:
        if self._damage_health == value:
            return

        pygame.event.post(
            pygame.Event(PLAYER_DAMAGE_HEALTH_CHANGED, amount=value - self._damage_health, new_value=value)
        )
        self._damage_health = value

    @property
    def arm_x(self) -> float:
        return self.x + self.width * (0.3 if self.facing is Side.LEFT else 0.7)

    @property
    def arm_y(self) -> float:
        return self.y + self.height * 0.7

    @property
    def front(self) -> float:
        return self.left if self.facing is Side.LEFT else self.right

    @property
    def slam_damage(self) -> int:
        return int(self.vy * Player.SLAM_DAMAGE)

    @property
    def slam_kb(self) -> Vec2:
        return Player.SLAM_KB[0] * self.vy, Player.SLAM_KB[1] * self.vy

    @property
    def interact_range(self) -> Rect:
        return (
            self.x - Player.INTERACT_RANGE,
            self.y - Player.INTERACT_RANGE,
            self.width + Player.INTERACT_RANGE * 2,
            self.height + Player.INTERACT_RANGE * 2,
        )

    @property
    def damage_mul(self) -> float:
        return self._damage_mul

    @damage_mul.setter
    def damage_mul(self, value: float) -> None:
        if self._damage_mul == value:
            return

        pygame.event.post(
            pygame.Event(PLAYER_DAMAGE_MULTIPLIER_CHANGED, amount=value - self._damage_mul, new_value=value)
        )
        pygame.event.post(
            pygame.Event(
                PLAYER_MULTIPLIERS_CHANGED, amount=value - self._damage_mul, new_value=value, multiplier="damage"
            )
        )
        self._damage_mul = value

    @property
    def health_mul(self) -> float:
        return self._health_mul

    @health_mul.setter
    def health_mul(self, value: float) -> None:
        if self._health_mul == value:
            return

        pygame.event.post(
            pygame.Event(PLAYER_HEALTH_MULTIPLIER_CHANGED, amount=value - self._health_mul, new_value=value)
        )
        pygame.event.post(
            pygame.Event(
                PLAYER_MULTIPLIERS_CHANGED, amount=value - self._health_mul, new_value=value, multiplier="health"
            )
        )
        self._health_mul = value

        # Update max & current health
        current_health = self.health / self.max_health
        self.max_health = int(Player.MAX_HEALTH * value)
        self.health = int(self.max_health * current_health)

    @property
    def sprint_mul(self) -> float:
        return Player.SPRINT_MULTIPLIER if self.sprinting else 1

    @property
    def is_moving(self) -> bool:
        return abs(self.controlled_vx) > 50

    @property
    def rolling(self) -> bool:
        return self.roll_time > 0

    @property
    def can_jump(self) -> bool:
        return not self.slamming and (self.jumps > 0 or self.wall_col_dir)

    # ---------------------------- Constructor ---------------------------- #

    def __init__(self):
        super().__init__(0, 0, Player.WIDTH, Player.HEIGHT)
        self.vx: float = 0  # The velocity of the player in the x direction (- left, + right)
        self.vy: float = 0  # The velocity of the player in the y direction (- up, + down)
        self.controlled_vx: float = 0  # The velocity of the player in the x direction caused by user controls
        self.sprinting: bool = False
        self.facing: Side = Side.RIGHT  # The direction the player is currently facing
        self.jumps: int = Player.JUMPS  # How many jumps the player has left (is reset when touching ground)
        self.roll_cooldown: float = 0  # The time until the player can roll again in seconds
        self.slamming: bool = False  # If the player is currently slamming
        self.on_platform: Wall | None = None
        self.roll_time: float = 0
        self.wall_col_dir: Side | None = None  # The direction of the collision with a wall (None if no collision)
        self.ledge_climbing: tuple[Side, Vec2] | None = None
        self.wall_climb_time: float = 0
        self._max_health: int = Player.MAX_HEALTH
        self._health: int = self.max_health
        self.i_frames: float = 0
        self._damage_health: float = 0
        self.weapon: Weapon = None
        self.damage_potions: int = 0
        self._damage_mul: float = 1  # Damage multiplier
        self.health_potions: int = 0
        self._health_mul: float = 1  # Health multiplier
        self.state: PlayerState = PlayerState.IDLE
        self.slam_dust_sprites: list[EffectSprite] = []
        self.jump_dust_sprites: list[EffectSprite] = []
        self.damage_tint_init_time: float = 0
        self.damage_tint_time: float = 0
        self.should_not_collide: set[Platform] = set()

        # Permanent attributes
        self.sprite: PlayerSprite = PlayerSprite("player/pink")
        self.slam_fall_sprite: EffectSprite = EffectSprite("Slam")
        sfx_folder = get_project_root() / "assets/sfx/player"
        self.walk_sfx: Sound = Sound(sfx_folder / "Walk.wav")
        self.sprint_sfx: Sound = Sound(sfx_folder / "Sprint.wav")
        self.jump_sfx: Sound = Sound(sfx_folder / "Jump.wav")
        self.land_sfx: Sound = Sound(sfx_folder / "Landing.wav")
        self.climb_sfx: Sound = Sound(sfx_folder / "Climb.wav")
        self.hit_sfx: Sound = Sound(sfx_folder / "Hit.wav", volume=0.6)

    # ------------------------------ Methods ------------------------------ #

    def to_default_values(self, x: float, y: float, facing: Side) -> None:
        self.x = x
        self.y = y
        self.facing = facing
        self.height = Player.HEIGHT
        self.vx = 0
        self.vy = 0
        self.controlled_vx = 0
        self.jumps = Player.JUMPS
        self.roll_cooldown = 0
        self.slamming = False
        self.on_platform = None
        self.roll_time = 0
        self.wall_col_dir = None
        self.ledge_climbing = None
        self.wall_climb_time = 0
        self.i_frames = 0
        self.damage_health = 0
        self.damage_tint_init_time = 0
        self.damage_tint_time = 0
        self.slam_dust_sprites.clear()
        self.jump_dust_sprites.clear()
        self.should_not_collide.clear()

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

        if not self.rolling and PlayerControl.LEFT in move_types:
            self._x_control(Side.LEFT, dt)

        if not self.rolling and PlayerControl.RIGHT in move_types:
            self._x_control(Side.RIGHT, dt)

        # NOTE: order matters for the below moves as they will override each other

        # Cannot jump if currently slamming or no jumps left
        if self.can_jump and PlayerControl.JUMP in move_types:
            self._jump()

        # Cannot roll if currently rolling or roll is on cooldown
        if not self.rolling and self.roll_cooldown <= 0 and PlayerControl.ROLL in move_types:
            self._roll()

        # Cannot slam if currently slamming or on a platform
        if not self.slamming and PlayerControl.SLAM in move_types:
            if self.on_platform:
                self.should_not_collide.add(self.on_platform)
            else:
                self._slam()

        if not (self.slamming or self.rolling or (self.wall_col_dir and not self.on_platform) or self.ledge_climbing):
            if PlayerControl.INTERACT in move_types:
                self._interact()
            elif self.weapon is not None:
                if PlayerControl.ATTACK_START in move_types:
                    self.weapon.start_attack()
                elif PlayerControl.ATTACK_STOP in move_types:
                    self.weapon.stop_attack()

    def _interact(self) -> None:
        for i in state.current_map.get_rect(*self.interact_range, lambda o: isinstance(o, Interactable)):
            i.interact()
            if isinstance(i, Gate):
                break

    def _interrupt_attack(self) -> None:
        if self.weapon:
            self.weapon.interrupt()

    def _x_control(self, direction: Side, dt: float) -> None:
        """Adds velocity (accelerates) in the x direction and changes facing direction.

        Parameters
        ----------
        direction : Side
            The direction of the acceleration.
        dt : float
            The number of seconds between this tick and the last tick.
        """

        # Cancel ledge climbing if not same direction
        if self.ledge_climbing is not None and self.ledge_climbing[0] != direction:
            self.ledge_climbing = None
        # Apply acceleration
        self.controlled_vx += Player.CONTROL_ACCEL * dt * direction.value * self.sprint_mul
        # Change direction facing
        self.facing = direction

    def _jump(self) -> None:
        """Jump... Cancel rolling + decrement jump + add jump velocity."""

        # Cancel roll if rolling
        if self.rolling:
            stopped_rolling = self._stop_rolling()
            if not stopped_rolling:
                return

        self.jump_sfx.play()

        # Cancel ledge climbing
        self.ledge_climbing = None

        # Reset sprite jump state time
        self.sprite.states[PlayerState.JUMPING.value].time = 0

        # Set vy to negative jump strength
        self.vy = -Player.JUMP_STRENGTH
        # Stop wall climbing so vy does not get overridden
        self.wall_climb_time = -1
        if self.wall_col_dir and not self.on_platform:
            # Set vx to opposing the wall to jump off
            self.controlled_vx = Player.WALL_JUMP_STRENGTH * -self.wall_col_dir.value
        else:
            # Do not consume a jump if wall jump
            self.jumps -= 1

    def _roll(self) -> None:
        """Cancel slam and ledge climbing + roll"""

        self.ledge_climbing = None
        if self.slamming:
            self.slamming = False
        self.sprite.states[PlayerState.ROLLING.value].time = 0
        self._interrupt_attack()
        self.roll_time = Player.ROLL_LENGTH

    def _stop_rolling(self) -> bool:
        """Stops the player from rolling if the player is able to stop rolling.

        Returns
        -------
        bool
            Whether the player stopped rolling or not.
        """

        walls_above = state.current_map.get_rect(
            self.x, self.y + self.height - Player.HEIGHT, self.width, Player.HEIGHT, lambda e: isinstance(e, Wall)
        )
        for wall in walls_above:
            if (
                wall.top < self.top + self.height - Player.HEIGHT < wall.bottom
                and wall.left < self.right
                and wall.right > self.left
            ):
                # Top when at base height inside wall and x inside wall
                return False

        self.roll_time = -1
        self.roll_cooldown = Player.ROLL_COOLDOWN
        return True

    def _slam(self) -> None:
        """Cancel roll + slam"""

        if self.rolling:
            stopped_rolling = self._stop_rolling()
            if not stopped_rolling:
                return
        self.wall_col_dir = None
        self.ledge_climbing = None
        self._interrupt_attack()

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

        # TODO Damage and move to good pos on exit map bottom
        return self.move(self.vx * dt, self.vy * dt)

    def handle_collisions(self, collisions: list[Collision]) -> None:
        """Handles player actions on collisions.

        Parameters
        ----------
        collisions : list of Direction
            The collisions the player experienced in this tick.
        """

        down_col = None

        for direction, entity in collisions:
            if direction is Direction.DOWN and isinstance(entity, Wall):
                down_col = entity
                break

        if down_col:
            self._handle_down_wall_collision(down_col)
        else:
            self.on_platform = None
            self.wall_col_dir = None

        if not self.slamming:
            reset_wall_climb = True
            for direction, entity in collisions:
                if (direction is Direction.RIGHT or direction is Direction.LEFT) and isinstance(entity, Wall):
                    if not self.rolling:
                        self._handle_side_wall_collision(direction.value, entity)
                    reset_wall_climb = False
                    break

            if reset_wall_climb:
                self._start_wall_climb.reset()

    def _handle_down_wall_collision(self, wall: Wall) -> None:
        """Actions on downwards wall collisions.

        This should be called from handle_collisions() and wrapped with run_once().
        """

        if self.slamming:
            self.slam_dust_sprites.append(EffectSprite("Slash_Cloud", self.center_x, self.bottom))
        elif self.jumps <= 0:
            self.jump_dust_sprites.append(EffectSprite("Jump_Dust", self.center_x, self.bottom))
            self.land_sfx.play()

        self.on_platform = wall
        self.jumps = Player.JUMPS
        self.slamming = False
        self.vy = 0
        self.wall_climb_time = -1

    def _handle_side_wall_collision(self, side: Side, wall: Wall) -> None:
        can_climb_ledge = self.top - wall.top < Player.HEIGHT * Player.LEDGE_CLIMB_HEIGHT

        if can_climb_ledge:
            can_climb_ledge = not [
                r
                for r in state.current_map.get_rect(
                    self.left - (1 if side is Side.LEFT else 0),
                    wall.top - Player.HEIGHT,
                    self.width + 1,
                    self.top - (wall.top - Player.HEIGHT),
                )
                if r is not wall
            ]

        left_key_down = key_handler.get_control(PlayerControl.LEFT)
        right_key_down = key_handler.get_control(PlayerControl.RIGHT)

        if can_climb_ledge:
            if side is Side.LEFT and left_key_down:
                self.ledge_climbing = side, (wall.right, wall.top)
            elif side is Side.RIGHT and right_key_down:
                self.ledge_climbing = side, (wall.left, wall.top)
        if left_key_down or right_key_down:
            self.wall_col_dir = side
            if not self.on_platform:
                self._interrupt_attack()
                if not can_climb_ledge:
                    self._start_wall_climb()

    @run_once
    def _start_wall_climb(self) -> None:
        self.wall_climb_time = Player.WALL_CLIMB_LENGTH

    def tick_changes(self, dt: float) -> None:
        """Updates values every tick.

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds
        """

        self.controlled_vx /= 1 + (Player.CONTROL_SPEED_DECAY / self.sprint_mul) * dt
        # Apply air resistance and friction
        if self.on_platform:
            self.vx /= 1 + Wall.FRICTION * dt  # Not how friction works but yes
        self.vx -= Map.get_air_resistance(self.vx, self.height) * dt
        self.vy -= Map.get_air_resistance(self.vy, self.width) * dt * 0.1

        # Tick invincibility frames
        self.i_frames -= dt
        self.damage_tint_time -= dt
        if self.damage_health > 0:
            self.damage_health -= max(8, self.damage_health) * Player.DAMAGE_HEALTH_DECAY * dt
            if self.damage_health < 0:
                self.damage_health = 0

        self._tick_roll(dt)

        if not self.slamming:
            # Apply gravity and cap at speed cap
            self.vy += Map.GRAVITY * dt
            if self.vy > Player.DROP_SPEED_CAP:
                self.vy = Player.DROP_SPEED_CAP
        elif self.vy <= Player.DROP_SPEED_CAP:
            # Stop slamming if below speed cap
            self.slamming = False

        if self.ledge_climbing is not None:
            self._tick_ledge_climb()
        self._tick_wall_col(dt)

    def _tick_wall_col(self, dt: float) -> None:
        if self.wall_col_dir and not (self.rolling and self.slamming and self.ledge_climbing):
            if self.wall_climb_time > 0:
                self.vy = -Player.WALL_CLIMB_STRENGTH
                self.wall_climb_time -= dt
            elif self.vy > 0:
                self.vy /= 1 + Wall.FRICTION * Player.GRAB_STRENGTH * dt

    def _tick_ledge_climb(self) -> None:
        side, target = self.ledge_climbing
        if not (key_handler.get_control(PlayerControl.LEFT) or key_handler.get_control(PlayerControl.RIGHT)) or (
            self.bottom <= target[1]
            and ((side is Side.RIGHT and self.left >= target[0]) or (side is Side.LEFT and self.right <= target[0]))
        ):
            self.ledge_climbing = None
            return

        self.controlled_vx = Player.HEIGHT * Player.LEDGE_CLIMB_SPEED * side.value
        if self.bottom >= target[1]:
            self.vy = -Player.HEIGHT * Player.LEDGE_CLIMB_SPEED

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

        if self.rolling:
            self.i_frames = 0.001
            # Reduce roll time and set vx to roll speed if rolling
            self.roll_time -= dt
            self.vx = Player.ROLL_SPEED * self.facing.value
            if not self.rolling:
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

        walls_above = state.current_map.get_rect(
            self.x, self.y + self.height - Player.HEIGHT, self.width, Player.HEIGHT, lambda e: isinstance(e, Wall)
        )
        if self.rolling:
            roll_height = clamp(
                int(Player.HEIGHT * _roll_height_fn(self.roll_time / Player.ROLL_LENGTH)),
                Player.HEIGHT,
                Player.MIN_HEIGHT,
            )

            do_change = True
            if roll_height > self.height:
                for wall in walls_above:
                    if (
                        wall.top < self.top + self.height - Player.HEIGHT < wall.bottom
                        and wall.left < self.right
                        and wall.right > self.left
                    ):
                        # Top when at base height inside wall and x inside wall
                        do_change = False

            if do_change:
                self.top += self.height - roll_height
                self.height = roll_height
            else:
                self.roll_time += dt
        elif self.height != Player.HEIGHT:
            # If not rolling and height is not base_height (e.g. when rolling is interrupted via jumping),
            # transition height to base height
            diff = Player.HEIGHT - self.height
            # If gap is small just snap it to base_height (if not it will never reach base_height)
            if diff < Player.HEIGHT / 10:
                new_top = self.top - diff
                new_height = Player.HEIGHT
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

    def heal(self, amount: int) -> None:
        if self.damage_health > 0:
            self.damage_health -= min(amount, self.damage_health)
        self.health = min(self.health + amount, self.max_health)

    def _regain_health(self, damage: int) -> None:
        # Health is int so if not >= 1 then it will be rounded to 0
        if self.damage_health >= 1 and self.health < self.max_health:
            damage /= 4  # Not full damage is regained
            if damage > self.damage_health:
                damage = self.damage_health
            self.damage_health -= damage
            self.health = min(int(self.health + damage), self.max_health)

    def tick_slam(self, dt: float) -> None:
        # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA CIRCULAR IMPORTSSSS
        from enemy.enemy import Enemy

        for enemy in state.current_map.get_rect(
            self.left - Player.SLAM_RANGE[0],
            self.top - Player.SLAM_RANGE[1],
            self.width + Player.SLAM_RANGE[0] * 2,
            self.height + Player.SLAM_RANGE[1] * 2,
            lambda e: isinstance(e, Enemy),
        ):
            falloff = 1 - abs(self.center_x - enemy.center_x) / (Player.SLAM_RANGE[0] * 2)
            kb_x, kb_y = self.slam_kb
            damage = enemy.take_hit(
                int(self.slam_damage * falloff),
                kb=(kb_x * falloff, kb_y * falloff),
                side=Side.LEFT if self.center_x > enemy.center_x else Side.RIGHT,
            )
            self._regain_health(damage)

    def tick_collision(self, dt: float) -> None:
        from enemy.enemy import Enemy

        for enemy in state.current_map.get_rect(*self, lambda e: isinstance(e, Enemy) and not e.dead):
            # Get as ratio, 1 is touching edges, 0 is exact same spot
            dx = (enemy.center_x - self.center_x) / ((self.width + enemy.width) / 2)
            dy = (enemy.center_y - self.center_y) / ((self.height + enemy.height) / 2)
            d = sqrt(dx**2 + dy**2)
            # Gravity equation, g = GM/r^2, epsilon so no division by 0
            gravity = ((Player.G * enemy.mass) / ((d + Player.ε) ** 2)) * dt
            self.vx -= min(Player.REPULSION_CAP, gravity) * (dx / d)
            if not self.slamming:
                # Prevent bouncing and make player slide off enemies
                self.vy -= (min(Player.REPULSION_CAP, gravity) / 30) * (dy / d)

    def tick_sprites(self, dt: float) -> None:
        self.sprite.tick(dt)

        to_remove = []
        for sprite in self.slam_dust_sprites + self.jump_dust_sprites:
            end = sprite.tick(dt)
            if end:
                to_remove.append(sprite)
        for sprite in to_remove:
            if sprite in self.slam_dust_sprites:
                self.slam_dust_sprites.remove(sprite)
            if sprite in self.jump_dust_sprites:
                self.jump_dust_sprites.remove(sprite)

    def tick_state(self, dt: float) -> None:
        if self.weapon and self.weapon.attacking:
            # Attack
            self.state = PlayerState.ATTACKING
        elif self.rolling or self.height < Player.HEIGHT:
            # Roll
            self.state = PlayerState.ROLLING
            # Replay mid roll animation if still
            roll_state = self.sprite.states[PlayerState.ROLLING.value]
            if self.height == Player.MIN_HEIGHT and roll_state.frame > 4:
                roll_state.frame = 2
        elif not self.on_platform:
            if self.wall_col_dir or self.ledge_climbing:
                # Climbing/sliding on wall
                if self.vy > 0:
                    self.state = PlayerState.WALL_SLIDING
                else:
                    self.state = PlayerState.CLIMBING
                    if not self.climb_sfx.playing:
                        self.climb_sfx.play(-1)

            else:
                # Not on platform so either jumping or falling
                self.state = PlayerState.JUMPING

                jump_state = self.sprite.states[PlayerState.JUMPING.value]
                # Skip to falling sprite when falling
                first_falling_frame = 1
                if self.vy > 0 and jump_state.frame < first_falling_frame:
                    jump_state.frame = first_falling_frame
                # Keep jump sprite at falling sprite when not on platform
                target_sprite = jump_state.num_sprites - (3 if self.is_moving else 2)
                if jump_state.frame > target_sprite:
                    jump_state.frame = target_sprite

                if self.slamming:
                    self.slam_fall_sprite.tick(dt)
        elif self.is_moving:
            # Walking/running
            if self.sprinting:
                self.state = PlayerState.SPRINTING
                if not self.sprint_sfx.playing:
                    self.sprint_sfx.play(-1)
                if self.walk_sfx.playing:
                    self.walk_sfx.fadeout(400)
            else:
                self.state = PlayerState.WALKING
                if not self.walk_sfx.playing:
                    self.walk_sfx.play(-1)
                if self.sprint_sfx.playing:
                    self.sprint_sfx.fadeout(300)
        else:
            # Idle if nothing else
            self.state = PlayerState.IDLE

    def stop_wrong_sfx(self) -> None:
        if not (self.on_platform and self.is_moving):
            if self.walk_sfx.playing:
                self.walk_sfx.fadeout(400)
            if self.sprint_sfx.playing:
                self.sprint_sfx.fadeout(300)

        if self.climb_sfx.playing and not (
            not self.on_platform and (self.wall_col_dir or self.ledge_climbing) and self.vy <= 0
        ):
            self.climb_sfx.fadeout(350)

    def tick(self, dt: float, moves: list[PlayerControl]) -> None:
        self.handle_moves(dt, *moves)
        self.tick_changes(dt)
        if self.weapon is not None:
            damage = self.weapon.tick(dt)
            self._regain_health(damage)
        if self.slamming:
            self.tick_slam(dt)
        if not self.rolling:
            self.tick_collision(dt)
        collisions = self.update_position(dt)
        self.handle_collisions(collisions)

        # Remove any platforms not currently colliding with
        self.should_not_collide &= set(state.current_map.get_rect(*self, lambda e: isinstance(e, Platform)))

        self.tick_sprites(dt)
        self.tick_state(dt)
        self.stop_wrong_sfx()

    def take_hit(self, damage: int, force: bool = False) -> None:
        if not force and self.i_frames > 0:
            return

        pygame.event.post(pygame.Event(PLAYER_HIT, damage=damage))

        self.hit_sfx.play()

        self.health -= damage
        self.damage_health += damage
        self.damage_tint_init_time = max(0.3, damage / 30)
        self.damage_tint_time = self.damage_tint_init_time

    def interrupt_all(self) -> None:
        if self.weapon:
            self.weapon.interrupt()
        self._stop_rolling()
        self.slamming = False

    def switch_weapon(self, weapon: Weapon) -> None:
        if self.weapon:
            self.weapon.interrupt()
            state.current_map.add_pickup(WeaponPickup(self.weapon, (self.center_x, self.center_y)))
        self.weapon = weapon
        pygame.event.post(pygame.Event(PLAYER_WEAPON_CHANGED, new_value=weapon))
        logger.debug(f"Weapon changed: {repr(weapon)}")

    def draw(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0):
        # super().draw(surface, (0, 255, 0), x_off, y_off)

        for dust_sprite in self.slam_dust_sprites:
            x = dust_sprite.x + x_off
            y = dust_sprite.y + y_off
            sprite = dust_sprite.get_current_sprite(Side.LEFT)
            surface.blit(sprite, (x - sprite.width, y - sprite.height))
            sprite = dust_sprite.get_current_sprite(Side.RIGHT)
            surface.blit(sprite, (x, y - sprite.height))

        for dust_sprite in self.jump_dust_sprites:
            sprite = dust_sprite.get_current_sprite(Side.RIGHT)  # Doesn't matter which side
            surface.blit(sprite, (dust_sprite.x + x_off - sprite.width / 2, dust_sprite.y + y_off - sprite.height))

        c_x_w_off = self.center_x + x_off
        b_y_w_off = self.bottom + y_off

        # Slam effect behind player sprite
        if self.slamming:
            sprite = self.slam_fall_sprite.get_current_sprite(Side.LEFT)
            surface.blit(sprite, (c_x_w_off - sprite.width, b_y_w_off - sprite.height * 0.8))
            sprite = self.slam_fall_sprite.get_current_sprite(Side.RIGHT)
            surface.blit(sprite, (c_x_w_off, b_y_w_off - sprite.height * 0.8))

        sprite = self.sprite.current_sprite
        surface.blit(sprite, (c_x_w_off - sprite.width / 2, b_y_w_off - sprite.height))

        if self.weapon is not None:
            self.weapon.draw(surface, (94, 101, 219), x_off, y_off)
