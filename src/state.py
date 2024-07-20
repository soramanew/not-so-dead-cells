import sys

import pygame
from util.event import DIFFICULTY_CHANGED, SCORE_CHANGED


class State:
    @property
    def difficulty(self) -> int:
        return self._difficulty

    @difficulty.setter
    def difficulty(self, value: int) -> None:
        if self._difficulty == value:
            return

        pygame.event.post(pygame.Event(DIFFICULTY_CHANGED, amount=value - self._difficulty, new_value=value))
        self._difficulty = value

    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, value: int) -> None:
        if self._score == value:
            return

        pygame.event.post(pygame.Event(SCORE_CHANGED, amount=value - self._score, new_value=value))
        self._score = value

    def __init__(self):
        self.current_map = None
        self.player = None
        self.camera = None
        self._difficulty = 1
        self._score = 0
        self.map_loaded = False

        self.hardcore = False

    def reset(self) -> None:
        self.current_map = None
        self.player = None
        self.camera = None
        self.difficulty = 1
        self.score = 0
        self.map_loaded = False


sys.modules[__name__] = State()
