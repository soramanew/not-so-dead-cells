import pygame.key


# The length that keys are held for (s)
_RETENTION_LENGTH: float = 0

# The dictionary of keys
_time: dict[int, float] = {}
# The dictionary of keys held
_held: dict[int, bool] = {}
# The dictionary containing whether the _keys dict should be used
_use: dict[int, bool] = {}


def tick(dt: float) -> None:
    for key, _ in filter(lambda i: i[1], _use.items()):
        _time[key] -= dt
        if _time[key] <= 0:
            _held[key] = False


def down(key: int) -> None:
    _held[key] = True
    _use[key] = False


def up(key: int) -> None:
    _time[key] = _RETENTION_LENGTH
    _use[key] = True


def get(key: int) -> bool:
    try:
        return _held[key]
    except KeyError:
        return False
