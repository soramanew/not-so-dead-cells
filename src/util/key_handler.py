import pygame

from .type import PlayerControl

# Time which counts as a tap, >= than this is not a tap
TAP_THRESHOLD: float = 0.3

# The dictionary of keys held
_held: dict[int, bool] = {}
# The time the keys have been held for
_time: dict[int, float] = {}


def tick(dt: float) -> None:
    for key, held in _held.items():
        if held:
            _time[key] += dt


def down(key: int) -> None:
    _held[key] = True
    _time[key] = 0


def up(key: int) -> float:
    """Releases the given key.

    Parameters
    ----------
    key : int
        The pygame key code of the key to release.

    Returns
    -------
    float
        The time the key has been held for.
    """

    _held[key] = False
    held = _time[key]
    _time[key] = 0
    return held


def get(key: int) -> bool:
    try:
        return _held[key]
    except KeyError:
        return False


def get_control(control: PlayerControl) -> bool:
    jump = get(pygame.K_w) or get(pygame.K_UP) or get(pygame.K_SPACE)
    if control is PlayerControl.LEFT:
        return get(pygame.K_a) or get(pygame.K_LEFT)
    elif control is PlayerControl.RIGHT:
        return get(pygame.K_d) or get(pygame.K_RIGHT)
    elif control is PlayerControl.SLAM:
        return (get(pygame.K_s) or get(pygame.K_DOWN)) and jump
    elif control is PlayerControl.JUMP:
        return jump
