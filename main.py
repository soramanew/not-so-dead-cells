from __future__ import annotations
import math

import pygame


# class Box:
#     def __init__(self, x: int, y: int, width: int, height: int, velocity: tuple[int, int] = None):
#         self.x = x
#         self.y = y
#         self.width = width
#         self.height = height
#         self.vx, self.vy = velocity if velocity else 0, 0
#         self.stationary = not bool(velocity)
#
#     @property
#     def x2(self):
#         return self.x + self.width
#
#     @property
#     def y2(self):
#         return self.y + self.height
#
#     @property  # UNUSED
#     def bounds(self) -> tuple[int, int, int, int]:
#         return self.x, self.y, self.x + self.width, self.y + self.height
#
#     def _is_colliding(self, box: Box) -> bool:
#         return self.x < box.x2 and self.x2 > box.x and self.y < box.y2 and self.y2 > box.y
#
#     def collide(self, box: Box):
#         if self.stationary and box.stationary:
#             return
#
#         if self._is_colliding(box):
#             pass


class Hitbox:
    def __init__(self, x: float, y: float, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.left = x
        self.top = y

    @property
    def x(self):
        """Alias for self.left"""
        return self.left

    @x.setter
    def x(self, value: float):
        self.left = value

    @property
    def y(self):
        """Alias for self.top"""
        return self.top

    @y.setter
    def y(self, value: float):
        self.top = value

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value: float):
        self._left = value
        self.rect.left = value

    @property
    def top(self):
        return self._top

    @top.setter
    def top(self, value: float):
        self._top = value
        self.rect.top = value

    @property
    def right(self):
        return self.left + self.rect.width

    @right.setter
    def right(self, value: float):
        self.left = value - self.rect.width
        self.rect.right = value

    @property
    def bottom(self):
        return self.top + self.rect.height

    @bottom.setter
    def bottom(self, value: float):
        self.top = value - self.rect.height
        self.rect.bottom = value

    def move(self, dx: float, dy: float, boxes: list[Hitbox]) -> list[str]:
        self.left += dx
        self.top += dy

        collisions = []

        for box in boxes:
            if self.rect.colliderect(box.rect):
                # if dx > 0:
                #     collisions.append("right")
                #     self.right = box.rect.left
                # if dx < 0:
                #     collisions.append("left")
                #     self.left = box.rect.right
                if dy > 0:
                    collisions.append("bottom")
                    self.bottom = box.rect.top
                if dy < 0:
                    collisions.append("top")
                    self.top = box.rect.bottom

        return collisions

    def draw(self, window: pygame.Surface):
        window.fill((0, 0, 255), self.rect)


class Player(Hitbox):
    SIDE_SPEED_ACCEL = 30
    SIDE_SPEED_CAP = 80

    JUMP_STRENGTH = 200
    ROLL_STRENGTH = 300
    SLAM_STRENGTH = 800

    # The number of jumps the player has
    JUMPS = 2
    # Slam length in seconds
    SLAM_LENGTH = 1
    # Roll cooldown in seconds
    ROLL_COOLDOWN = 0.5

    # The decay of the rolling velocity
    ROLL_VX_DECAY = 3
    # The decay of the velocity added by controlling the player
    CONTROL_VX_DECAY = 10
    # The decay of the slamming velocity
    SLAM_VY_DECAY = 1

    def __init__(self, x: float, y: float):
        super().__init__(x, y, 10, 30)
        self.jumps = 2  # How many jumps the player has left (is reset when touching ground)
        self.rolling = False  # If the player is currently rolling
        self.roll_cooldown = 0  # The time until the player can roll again in seconds
        self.roll_vx = 0  # The velocity added by rolling
        self.facing = 1  # The direction the player is currently facing (-1 for left, 1 for right)
        self.controlled_vx = 0  # The controlled velocity of the player in the x direction (- is left, + is right)
        self.general_vy = 0  # The general (not slamming) velocity in the y direction (- is up, + is down)
        self.slamming = False  # If the player is currently slamming
        self.slam_vy = 0  # The velocity added by slamming

    @property
    def vx(self):
        return self.controlled_vx + self.roll_vx

    @vx.setter
    def vx(self, value):
        total_vx = self.vx or 1
        self.controlled_vx = value * (self.controlled_vx / total_vx)
        self.roll_vx = value * (self.roll_vx / total_vx)

    @property
    def vy(self):
        return self.general_vy + self.slam_vy

    @vy.setter
    def vy(self, value):
        total_vy = self.vy or 1
        self.general_vy = value * (self.general_vy / total_vy)
        self.slam_vy = value * (self.slam_vy / total_vy)

    @property
    def rolling(self):
        return self._rolling

    @rolling.setter
    def rolling(self, value: bool):
        self._rolling = value
        # Reset cooldown on stop rolling
        if not value:
            self.roll_cooldown = Player.ROLL_COOLDOWN

    def handle_moves(self, *move_types: str):
        if "left" in move_types:
            if self.facing > 0:
                self.controlled_vx -= Player.SIDE_SPEED_ACCEL
            elif abs(self.controlled_vx) < Player.SIDE_SPEED_CAP:
                if abs(self.controlled_vx - Player.SIDE_SPEED_ACCEL) <= Player.SIDE_SPEED_CAP:
                    self.controlled_vx -= Player.SIDE_SPEED_ACCEL
                else:
                    self.controlled_vx = -Player.SIDE_SPEED_CAP
            self.facing = -1

        if "right" in move_types:
            if self.facing < 0:
                self.controlled_vx += Player.SIDE_SPEED_ACCEL
            elif abs(self.controlled_vx) < Player.SIDE_SPEED_CAP:
                self.controlled_vx += Player.SIDE_SPEED_ACCEL
                if abs(self.controlled_vx) > Player.SIDE_SPEED_CAP:
                    self.controlled_vx = Player.SIDE_SPEED_CAP
            self.facing = 1

        # Add upwards velocity on jump
        if self.jumps > 0 and "jump" in move_types:
            # Cancel roll if rolling
            if self.rolling:
                self.rolling = False
            self.jumps -= 1
            self.general_vy = -Player.JUMP_STRENGTH

        # Add forwards velocity on roll; Cannot roll if roll is on cooldown
        if not self.rolling and self.roll_cooldown <= 0 and "roll" in move_types:
            # Cancel slam if slamming
            if self.slamming:
                self.slamming = False
            self.rolling = True
            self.roll_vx += Player.ROLL_STRENGTH * self.facing
            # TODO: change hitbox when rolling

        if not self.slamming and "slam" in move_types:
            if self.rolling:
                self.rolling = False
            self.slamming = True
            self.slam_vy += Player.SLAM_STRENGTH

    def update_position(self, dt: float, boxes: list[Hitbox]):
        collisions = super().move(self.vx * dt, self.vy * dt, boxes)

        if "bottom" in collisions:
            self.jumps = 2
            self.slamming = False
            self.vy = 0
            self.vx /= 1 + World.FRICTION

        # TODO: climb ledges, wall climbing

    def tick_changes(self, dt):
        """Updates the values which change per tick

        Parameters
        ----------
        dt : float
            The time between this tick and the last tick in seconds
        """

        # Decay velocities
        self.controlled_vx /= 1 + Player.CONTROL_VX_DECAY * dt
        self.roll_vx /= 1 + Player.ROLL_VX_DECAY * dt
        self.slam_vy /= 1 + Player.SLAM_VY_DECAY * dt

        # Apply gravity
        self.general_vy += World.GRAVITY * dt

        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt
        if self.rolling and abs(self.roll_vx) <= 20:
            self.rolling = False


class World:
    GRAVITY = 300
    FRICTION = 0.1


def main():
    pygame.init()

    size = 800, 400
    window = pygame.display.set_mode(size)
    clock = pygame.time.Clock()

    player = Player(60, 60)

    boxes = [Hitbox(10, 300, 780, 80)]

    while True:
        dt = clock.tick(60) / 1000  # To get in seconds

        move_types = []

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_types.append("left")
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_types.append("right")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and event.key == pygame.K_SPACE:
                    move_types.append("slam")
                elif event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
                    move_types.append("jump")
                elif event.key == pygame.K_LSHIFT:
                    move_types.append("roll")

        player.handle_moves(*move_types)
        player.update_position(dt, boxes)
        player.tick_changes(dt)

        # Clear window
        window.fill((0, 0, 0))

        for box in boxes:
            box.draw(window)
        player.draw(window)

        # Update window
        pygame.display.update()


if __name__ == '__main__':
    main()
