from abc import ABC, abstractmethod
from random import uniform


class Modifier(ABC):
    @abstractmethod
    def to_friendly_str(self) -> str:
        pass


class DamageMod(Modifier):
    def __init__(self):
        self.damage = round(uniform(0.8, 1.5), 2)

    def to_friendly_str(self) -> str:
        return f"Damage x{self.damage}"
