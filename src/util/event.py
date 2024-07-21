import sys

import pygame

_counter = pygame.USEREVENT + 1


def add_events(*events: str, prefix: str = "", suffix: str = "") -> None:
    if prefix:
        prefix += "_"  # Add underscore separator
    if suffix:
        suffix = "_" + suffix

    global _counter
    for event in events:
        setattr(sys.modules[__name__], (prefix + event + suffix).upper(), _counter)
        _counter += 1


add_events("hit", prefix="player")
add_events(
    "health",
    "max_health",
    "damage_health",
    "damage_multiplier",
    "health_multiplier",
    "multipliers",
    "weapon",
    prefix="player",
    suffix="changed",
)
add_events("button_pressed", prefix="ui")
add_events("difficulty", "score", "loading_progress", suffix="changed")
