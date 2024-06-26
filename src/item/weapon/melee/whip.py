import math

from item.modifier import Modifier

from .melee import MeleeWeapon


class CattleDriver(MeleeWeapon):
    @property
    def current_time(self) -> float:
        return ((self.atk_length - self.atk_time) / self.atk_length) * math.pi

    @MeleeWeapon.top.getter
    def top(self) -> float:
        time = math.cos(self.current_time * 2) / 2
        if time < 0:
            time = 0
        return self.atk_top + (self.atk_height - self.height) * time

    @property
    def width(self) -> int:
        return int(self.atk_width * math.sin(self.current_time))

    @width.setter
    def width(self, value: int) -> None:
        pass

    @property
    def height(self) -> int:
        return int(self.atk_height * math.sin(self.current_time))

    @height.setter
    def height(self, value: int) -> None:
        pass

    def __init__(self, modifiers: list[Modifier]):
        super().__init__(
            name="Cattle Driver",
            desc="This doesn't seem to have been used for driving cattle...",
            width=0,
            height=0,
            atk_width=60,
            atk_height=35,
            damage=24,
            atk_windup=0.3,
            atk_length=0.2,
            kb=(70, -50),
            modifiers=modifiers,
        )
