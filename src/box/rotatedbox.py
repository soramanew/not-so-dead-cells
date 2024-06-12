from __future__ import annotations

import math

import pygame
from util.type import Line, Vec2

from .box import Box


def _rotate(x: float, y: float, angle: float) -> Vec2:
    cos = math.cos(angle)
    sin = math.sin(angle)
    return x * cos - y * sin, y * sin + y * cos


def _project(v: Vec2, line: Line) -> Vec2:
    line_origin, line_dst = line
    dot = line_dst[0] * (v[0] - line_origin[0]) + line_dst[1] * (v[1] - line_origin[1])
    return line_origin[0] + line_dst[0] * dot, line_origin[1] + line_dst[1] * dot


def _magnitude(x: float, y: float) -> float:
    return x * x + y * y


def _axis_colliding(
    box: Box | RotatedBox, axis: Line, half_rect: float, corners: tuple[Vec2, Vec2, Vec2, Vec2]
) -> bool:
    min_dst = None
    max_dst = None

    for corner in corners:
        projected = _project(corner, axis)
        centered_projected = projected[0] + box.center_x, projected[1] + box.center_y
        sign = centered_projected[0] * axis[1][0] + centered_projected[1] * axis[1][1] > 0
        signed_distance = _magnitude(*centered_projected) * (1 if sign else -1)

        if min_dst is None or min_dst > signed_distance:
            min_dst = signed_distance
        if max_dst is None or max_dst < signed_distance:
            max_dst = signed_distance

    if not (min_dst < 0 and max_dst > 0 or abs(min_dst) < half_rect or abs(max_dst) < half_rect):
        return False


def _projection_colliding(box1: Box | RotatedBox, box2: Box | RotatedBox, axes: tuple[Line, Line]) -> bool:
    corners = (box2.left, box2.top), (box2.right, box2.top), (box2.left, box2.bottom), (box2.right, box2.bottom)
    return _axis_colliding(box1, axes[0], box1.width / 2, corners) and _axis_colliding(
        box1, axes[1], box1.height / 2, corners
    )


class RotatedBox:
    @property
    def x(self) -> float:
        return self.left

    @property
    def y(self) -> float:
        return self.top

    @property
    def top_left(self) -> Vec2:
        return self._rotate_point(
            self.anchor_x - self.width * self.anchor_xr, self.anchor_y - self.height * self.anchor_yr
        )

    @property
    def left(self) -> float:
        return self.top_left[0]

    @property
    def top(self) -> float:
        return self.top_left[1]

    @property
    def bottom_right(self) -> Vec2:
        return self._rotate_point(
            self.anchor_x + self.width * (1 - self.anchor_xr), self.anchor_y + self.height * (1 - self.anchor_yr)
        )

    @property
    def right(self) -> float:
        return self.bottom_right[0]

    @property
    def bottom(self) -> float:
        return self.bottom_right[1]

    @property
    def center(self) -> Vec2:
        return self._rotate_point(
            self.anchor_x + self.width * (0.5 - self.anchor_xr),
            self.anchor_y + self.height * (0.5 - self.anchor_yr),
            (self.anchor_x, self.anchor_y),
        )

    @property
    def center_x(self) -> float:
        return self.center[0]

    @property
    def center_y(self) -> float:
        return self.center[1]

    def __init__(
        self,
        anchor_x: float,
        anchor_y: float,
        width: int,
        height: int,
        angle: float,
        anchor_xr: float = 0.5,
        anchor_yr: float = 0.5,
    ):
        self.anchor_x: float = anchor_x
        self.anchor_y: float = anchor_y
        self.width: int = width
        self.height: int = height
        self.angle: float = angle  # The angle it makes with the right horizontal (radians)
        self.anchor_xr: float = anchor_xr  # The point of the anchor along the width (0 = left, 1 = right)
        self.anchor_yr: float = anchor_yr  # The point of the anchor along the height (0 = top, 1 = bottom)

    def _rotate_point(self, x: float, y: float, center: Vec2 = None) -> Vec2:
        cx, cy = self.center if center is None else center
        temp_x = x - cx
        temp_y = y - cy
        cos = math.cos(self.angle)
        sin = math.sin(self.angle)
        rot_x = temp_x * cos - temp_y * sin
        rot_y = temp_x * sin + temp_y * cos
        return rot_x + cx, rot_y + cy

    def _get_axes(self) -> tuple[Line, Line]:
        x_axis = _rotate(1, 0, self.angle)
        y_axis = _rotate(0, 1, self.angle)
        cx, cy = self.center
        return ((cx, cy), x_axis), ((cx, cy), y_axis)

    def detect_collision(self, box: Box) -> bool:
        return _projection_colliding(
            box, self, (((box.center_x, box.center_y), (1, 0)), ((box.center_x, box.center_y), (0, 1)))
        ) and _projection_colliding(self, box, self._get_axes())

    def draw(
        self,
        window: pygame.Surface,
        colour: tuple[int, int, int] = (0, 0, 255),
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        """Draws this box to the given surface.

        Parameters
        ----------
        window : pygame.Surface
            The surface to draw to.
        colour : tuple[int, int, int], default = (0, 0, 255)
            The colour to draw this box as.
        x_off : float, default = 0
            The offset in the x direction to draw this box.
        y_off : float, default = 0
            The offset in the y direction to draw this box.
        scale : float, default = 1
            The scale to draw this box.
        """

        left = (self.left + x_off) * scale
        top = (self.top + y_off) * scale
        right = (self.right + x_off) * scale
        bottom = (self.bottom + y_off) * scale
        pygame.draw.polygon(window, colour, ((left, top), (right, top), (right, bottom), (left, bottom)))
