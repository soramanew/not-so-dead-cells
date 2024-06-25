from item.modifier import Modifier

from .melee import MeleeWeapon


class RustySword(MeleeWeapon):
    def __init__(self, modifiers: list[Modifier]):
        super().__init__(
            name="Rusty Ol' Sword",
            desc="A rusty sword you found in the depths of your shed.",
            width=40,
            height=10,
            atk_width=40,
            atk_height=40,
            damage=30,
            atk_windup=0.3,
            atk_length=0.2,
            kb=(100, -80),
            modifiers=modifiers,
        )
