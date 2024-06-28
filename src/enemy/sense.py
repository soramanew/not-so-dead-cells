import pygame
import state
from map import Wall
from util.func import line_line, normalise_for_drawing
from util.type import Colour, EnemyState, Line, Rect

from .enemyabc import EnemyABC


def _line_rect(line: Line, rect: Rect) -> bool:
    """Line to rectangle intersection."""
    left, top, width, height = rect
    right = left + width
    bottom = top + height
    return (
        line_line(line, ((left, top), (left, bottom)))
        or line_line(line, ((left, top), (right, top)))
        or line_line(line, ((right, bottom), (left, bottom)))
        or line_line(line, ((right, bottom), (right, top)))
    )


class Sense(EnemyABC):
    @property
    def sense_x(self) -> float:
        return self.head_x - self._get_dep_facing(self._sense_x) * self.sense_width

    @property
    def sense_y(self) -> float:
        return self.head_y - self._sense_y

    @property
    def sense_area(self) -> Rect:
        return self.sense_x, self.sense_y, self.sense_width, self.sense_height

    @property
    def alerting(self) -> bool:
        """If the enemy has been alerted and is playing the animation."""
        return self.alert_time > 0

    def __init__(
        self,
        sense_x: float,
        sense_y: float,
        sense_width: int,
        sense_height: int,
        xray: bool,
        alert_delay: float,
        alert_retain_length: float,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._sense_x: float = sense_x
        self._sense_y: float = sense_y * sense_height
        self.sense_width: int = sense_width
        self.sense_height: int = sense_height
        self.xray: bool = xray
        self.alert_delay: float = alert_delay
        self.alert_retain_length: float = alert_retain_length

        self.can_sense_player: bool = False
        self.alerted: bool = False  # Alerted but not necessarily able to sense player (alert retention)
        self._alerting: bool = False
        self.alert_time: float = 0
        self.alert_retain_time: float = 0

        self._sense_surface: pygame.Surface = pygame.Surface((sense_width, sense_height)).convert()
        self._sense_surface.set_alpha(40)

    def check_for_player(self) -> bool:
        player_in_bounds = state.player.detect_collision_rect(*self.sense_area)

        # Early return if xray or player isn't in sense area
        if self.xray or not player_in_bounds:
            return player_in_bounds

        obstacles = state.current_map.get_rect(*self.sense_area, lambda o: isinstance(o, Wall))
        head = self.head_x, self.head_y
        p_left, p_top, p_right, p_bottom = state.player.left, state.player.top, state.player.right, state.player.bottom

        intersections = 0
        for corner in (p_left, p_top), (p_left, p_bottom), (p_right, p_top), (p_right, p_bottom):
            for o in obstacles:
                if _line_rect((head, corner), o):
                    intersections += 1
                    break

        # If all 4 lines to player corners intersect an object, player is not visible
        return intersections < 4

    def _tick_sense(self, dt: float) -> None:
        self.can_sense_player = self.check_for_player()

        # Start alerting (idk if this is even a word)
        if self.can_sense_player and not (self.alerted or self.alerting):
            self.alert_time = self.alert_delay
            self._alerting = True
            self.states[EnemyState.ATTACKING.value].time = 0

        # Idk why this has to be here, I tried moving it to above and below but it just gets stuck alerting
        self.alert_time -= dt

        # Set state
        if self.alerting:
            self.state = EnemyState.ALERTED
        elif self._alerting:
            # End alerting if alerting done but flag not set
            self._alerting = False
            self.alerted = True

        # If can sense player, reset retention time
        if self.can_sense_player:
            self.alert_retain_time = self.alert_retain_length

        self.alert_retain_time -= dt

        # Alerted and retention time ended
        if self.alerted and self.alert_retain_time <= 0:
            self.alerted = False

    def draw_sense(
        self,
        surface: pygame.Surface,
        colours: tuple[Colour, Colour],
        x_off: float,
        y_off: float,
        scale: float,
    ) -> None:
        x, y, width, height = normalise_for_drawing(*self.sense_area, x_off, y_off, scale)
        if width <= 0 or height <= 0:
            return

        colour = colours[1 if self.alerted else 0]
        self._sense_surface.fill(colour)

        s2 = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        if state.player.detect_collision_rect(*self.sense_area):
            head = self.head_x, self.head_y
            head_off = (head[0] + x_off) * scale, (head[1] + y_off) * scale
            p_left, p_top, p_right, p_bottom = (
                state.player.left,
                state.player.top,
                state.player.right,
                state.player.bottom,
            )
            if self.xray:
                for corner in (p_left, p_top), (p_left, p_bottom), (p_right, p_top), (p_right, p_bottom):
                    pygame.draw.line(
                        s2, (*colour, 120), head_off, ((corner[0] + x_off) * scale, (corner[1] + y_off) * scale)
                    )
            else:
                obstacles = state.current_map.get_rect(*self.sense_area, lambda o: isinstance(o, Wall))
                for corner in (p_left, p_top), (p_left, p_bottom), (p_right, p_top), (p_right, p_bottom):
                    intersects = False
                    for o in obstacles:
                        if _line_rect((head, corner), o):
                            intersects = True
                            break
                    pygame.draw.line(
                        s2,
                        (*colours[0 if intersects else 1], 120),
                        head_off,
                        ((corner[0] + x_off) * scale, (corner[1] + y_off) * scale),
                    )

        surface.blit(self._sense_surface, (x, y))
        surface.blit(s2, (0, 0))
