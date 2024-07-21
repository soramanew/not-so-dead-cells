import sys

import pygame
from util.event import DIFFICULTY_CHANGED, LOADING_PROGRESS_CHANGED, SCORE_CHANGED


class State:
    @property
    def difficulty(self) -> float:
        return self._difficulty

    @difficulty.setter
    def difficulty(self, value: float) -> None:
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

    @property
    def loading_progress(self) -> float:
        return self._loading_progress

    @loading_progress.setter
    def loading_progress(self, value: float) -> None:
        if self._loading_progress == value:
            return

        pygame.event.post(
            pygame.Event(LOADING_PROGRESS_CHANGED, amount=value - self._loading_progress, new_value=value)
        )
        self._loading_progress = value

    def __init__(self):
        self.current_map = None
        self.player = None
        self.camera = None
        self._difficulty: float = 1
        self._score: int = 0
        self.map_loaded: bool = False
        self._loading_progress: float = 0

        self.hardcore: bool = False

    def reset(self) -> None:
        self.current_map = None
        self.player = None
        self.camera = None
        self.difficulty = 1
        self.score = 0
        self.map_loaded = False


sys.modules[__name__] = State()
