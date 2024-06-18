import pygame
from map import Wall
from util.func import line_line, normalise_for_drawing
from util.type import Colour, Line, Rect

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

    def __init__(self, sense_x: float, sense_y: float, sense_width: int, sense_height: int, xray: bool, **kwargs):
        super().__init__(**kwargs)
        self._sense_x: float = sense_x
        self._sense_y: float = sense_y * sense_height
        self.sense_width: int = sense_width
        self.sense_height: int = sense_height
        self.xray: bool = xray

    def check_for_player(self) -> bool:
        player_in_bounds = self.player.detect_collision_rect(*self.sense_area)

        # Early return if xray or player isn't in sense area
        if self.xray or not player_in_bounds:
            return player_in_bounds

        obstacles = self.map.get_rect(*self.sense_area, lambda o: isinstance(o, Wall))
        head = self.head_x, self.head_y
        p_left, p_top, p_right, p_bottom = self.player.left, self.player.top, self.player.right, self.player.bottom

        intersections = 0
        for corner in (p_left, p_top), (p_left, p_bottom), (p_right, p_top), (p_right, p_bottom):
            for o in obstacles:
                if _line_rect((head, corner), o):
                    intersections += 1
                    break

        # If all 4 lines to player corners intersect an object, player is not visible
        return intersections < 4

    def _tick_sense(self) -> None:
        self.alerted = self.check_for_player()

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

        s = pygame.Surface((width, height))
        s.set_alpha(20)
        colour = colours[1 if self.alerted else 0]
        s.fill(colour)

        s2 = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        if self.player.detect_collision_rect(*self.sense_area):
            head = self.head_x, self.head_y
            head_off = (head[0] + x_off) * scale, (head[1] + y_off) * scale
            p_left, p_top, p_right, p_bottom = self.player.left, self.player.top, self.player.right, self.player.bottom
            if self.xray:
                for corner in (p_left, p_top), (p_left, p_bottom), (p_right, p_top), (p_right, p_bottom):
                    pygame.draw.line(
                        s2, (*colour, 120), head_off, ((corner[0] + x_off) * scale, (corner[1] + y_off) * scale)
                    )
            else:
                obstacles = self.map.get_rect(*self.sense_area, lambda o: isinstance(o, Wall))
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

        surface.blit(s, (x, y))
        surface.blit(s2, (0, 0))
