from pathlib import Path


def get_project_root():
    """Returns path of the root project directory."""
    return Path(__file__).parent.parent


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


def normalise_rect(x: float, y: float, width: int, height: int) -> tuple[float, float, int, int]:
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
    tuple[float, float, int, int]
        The rectangle with a positive width and height.
    """

    if width < 0:
        x += width
        width *= -1
    if height < 0:
        y += height
        height *= -1
    return x, y, width, height
