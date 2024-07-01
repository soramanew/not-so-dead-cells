from pathlib import Path

import pygame

from .type import Colour, Line, Rect, Vec2


def get_project_root():
    """Returns path of the root project directory."""
    return Path(__file__).parent.parent  # NOTE 2 parents when packaging


def get_font(family: str, size: int, weight: str = "Regular") -> pygame.font.Font:
    fonts_dir = get_project_root() / "assets/fonts"
    ttf = fonts_dir / f"{family}-{weight}.ttf"
    return pygame.font.Font(ttf if ttf.is_file() else (fonts_dir / f"{family}-{weight}.otf"), size)


def get_fps() -> int:
    return pygame.display.get_current_refresh_rate() or 60


def clamp(x: int, maximum: int, minimum: int) -> int:
    """Clamps a value to the range [minimum, maximum].

    Parameters
    ----------
    x : int
        The value to clamp
    maximum : int
        The maximum value
    minimum : int
        The minimum value

    Returns
    -------
    int
        The clamped value
    """
    return min(maximum, max(minimum, x))


def normalise_rect(x: float, y: float, width: int, height: int) -> Rect:
    """Normalises the given rectangle so the width and height are positive.

    Parameters
    ----------
    x : float
        The left-most x coordinate of the rectangle. If the width is negative this is actually the right-most.
    y : float
        The top-most y coordinate of the rectangle. If the height is negative this is actually the bottom-most.
    width : int
        The width of the rectangle. Can be negative.
    height : int
        The height of the rectangle. Can be negative.

    Returns
    -------
    Rect
        The rectangle with a positive width and height.
    """

    if width < 0:
        x += width
        width *= -1
    if height < 0:
        y += height
        height *= -1
    return x, y, width, height


def line_line(l1: Line, l2: Line) -> Vec2 | None:
    """Line to line intersection.

    Credit to https://www.jeffreythompson.org/collision-detection/line-line.php

    Parameters
    ----------
    l1 : Line
        The first line.
    l2 : Line
        The second line.

    Returns
    -------
    Vec2 | None
        The intersection point or None if not intersecting.
    """

    (x1, y1), (x2, y2) = l1
    (x3, y3), (x4, y4) = l2
    denominator = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denominator:
        u_a = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denominator
        u_b = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denominator
        if 0 <= u_a <= 1 and 0 <= u_b <= 1:
            return x1 + (u_a * (x2 - x1)), y1 + (u_a * (y2 - y1))
    return None


def normalise_for_drawing(
    x: float, y: float, width: int, height: int, x_off: float = 0, y_off: float = 0, scale: float = 1
) -> Rect:
    x = (x + x_off) * scale
    y = (y + y_off) * scale
    width *= scale
    height *= scale
    if x < 0:
        width += x
        x = 0
    if y < 0:
        height += y
        y = 0
    return x, y, width, height


def render_interact_text(text: str, colour: Colour = (255, 255, 255)) -> pygame.Surface:
    # Damn it I have to create the font here because if not pygame.font won't be initialized yet
    return pygame.font.SysFont("Readex Pro", 16).render(f"[F] {text}", True, colour)
