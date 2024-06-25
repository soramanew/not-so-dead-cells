from item.modifier import Modifier

from .melee import MeleeWeapon


class NutCracker(MeleeWeapon):
    def __init__(self, modifiers: list[Modifier]):
        super().__init__(
            name="Nut Cracker",
            desc="Cracks nuts. What's more to say?",
            width=30,
            height=20,
            atk_width=30,
            atk_height=50,
            damage=60,
            atk_windup=0.5,
            atk_length=0.2,
            kb=(150, -120),
            modifiers=modifiers,
        )
