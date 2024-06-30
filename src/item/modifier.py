from __future__ import annotations

from abc import ABC, abstractmethod
from random import uniform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .item import Item
    from .weapon.melee.melee import MeleeWeapon


class Modifier(ABC):
    @abstractmethod
    def apply(self, item: Item) -> None:
        pass

    @abstractmethod
    def to_friendly_str(self) -> str:
        pass


class DamageMod(Modifier):
    def __init__(self):
        self.damage = round(uniform(0.8, 1.3), 2)

    def apply(self, item: Item) -> None:
        item.damage = int(item.damage * self.damage)

    def to_friendly_str(self) -> str:
        return f"Damage x{self.damage}"


class SpeedMod(Modifier):
    def __init__(self):
        self.speed = round(uniform(0.8, 1.3), 2)

    def apply(self, weapon: MeleeWeapon) -> None:
        weapon.atk_windup /= self.speed
        weapon.atk_length /= self.speed
        weapon.sprite_obj.speed *= self.speed

    def to_friendly_str(self) -> str:
        return f"Attack speed x{self.speed}"
