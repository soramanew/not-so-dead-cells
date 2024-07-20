import sys

import pygame

_counter = pygame.USEREVENT + 1


def add_events(*events: str, prefix: str = "") -> None:
    if prefix:
        prefix += "_"  # Add underscore separator

    global _counter
    for event in events:
        setattr(sys.modules[__name__], (prefix + event).upper(), _counter)
        _counter += 1


add_events(
    "hit",
    "health_changed",
    "max_health_changed",
    "damage_health_changed",
    "damage_multiplier_changed",
    "health_multiplier_changed",
    "multipliers_changed",
    "weapon_changed",
    prefix="player",
)
add_events("button_pressed", prefix="ui")
add_events("difficulty_changed", "score_changed")
