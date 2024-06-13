from pathlib import Path

from .type import Line, Rect, Vec2


def get_project_root():
    """Returns path of the root project directory."""
    return Path(__file__).parent.parent.parent


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


def comp_as_int(a: float, b: float) -> bool:
    """Compares two floats by casting them to ints first then comparing.

    Parameters
    ----------
    a : float
        A float to compare.
    b : float
        The other float to compare.

    Returns
    -------
    If the int representations of the two floats are equal.
    """

    return int(a) == int(b)


def strict_eq(a, b) -> bool:
    """Checks if the classes of both parameters are the same.

    Parameters
    ----------
    a : Any
        The first element to compare.
    b : Any
        The other element to compare.

    Returns
    -------
    Whether the two elements are the same class.
    """

    return type(a).__name__ == type(b).__name__


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
    u_a = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    u_b = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    if 0 <= u_a <= 1 and 0 <= u_b <= 1:
        return x1 + (u_a * (x2 - x1)), y1 + (u_a * (y2 - y1))
    return None
