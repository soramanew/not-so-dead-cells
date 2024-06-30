from constants import SPRITES_PER_SECOND
from item.modifier import Modifier

from .melee import MeleeWeapon


def _attack_length(speed: float) -> float:
    return (1 / (SPRITES_PER_SECOND * speed)) * 4


class RustySword(MeleeWeapon):
    def __init__(self, modifiers: list[Modifier]):
        super().__init__(
            name="Rusty Ol' Sword",
            desc="A rusty sword you found in the depths of your shed.",
            sprite="Rusty_Sword",
            sprite_frames=8,
            sprite_speed=1.5,
            width=50,
            height=15,
            atk_width=50,
            atk_height=70,
            damage=30,
            atk_windup=_attack_length(1.5),
            atk_length=_attack_length(1.5),
            kb=(100, -80),
            modifiers=modifiers,
        )


class NutCracker(MeleeWeapon):
    def __init__(self, modifiers: list[Modifier]):
        super().__init__(
            name="Nut Cracker",
            desc="Can this even be considered a sword?",
            sprite="Nut_Cracker",
            sprite_frames=8,
            sprite_speed=1,
            width=50,
            height=20,
            atk_width=50,
            atk_height=80,
            damage=60,
            atk_windup=_attack_length(1),
            atk_length=_attack_length(1),
            kb=(150, -120),
            modifiers=modifiers,
        )
