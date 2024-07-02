from abc import abstractmethod

import state
from box import Hitbox

from ..item import Item


class Weapon(Hitbox, Item):
    @property
    @abstractmethod
    def left(self) -> float:
        pass

    @left.setter
    def left(self, value):
        pass

    @property
    @abstractmethod
    def top(self) -> float:
        pass

    @top.setter
    def top(self, value):
        pass

    def __init__(self, damage: int, **kwargs):
        self.damage: int = int(damage * state.difficulty * 0.5)  # Scales less than difficulty
        self.atk_time: float = 0
        super().__init__(x=0, y=0, **kwargs)

    @abstractmethod
    def start_attack(self) -> None:
        pass

    @abstractmethod
    def stop_attack(self) -> None:
        pass

    @abstractmethod
    def interrupt(self) -> None:
        pass

    @abstractmethod
    def tick(self, dt: float) -> int:
        pass
