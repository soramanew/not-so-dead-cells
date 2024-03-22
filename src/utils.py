from pathlib import Path


def get_project_root():
    """Returns path of the root project directory."""
    return Path(__file__).parent.parent


def clamp(x, maximum, minimum):
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
