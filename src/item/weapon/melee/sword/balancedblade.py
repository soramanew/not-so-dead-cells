from item.modifier import Modifier

from .sword import Sword


class BalancedBlade(Sword):
    def __init__(self, modifiers: list[Modifier]):
        super().__init__(
            name="Balanced Blade",
            width=20,
            height=10,
            atk_width=20,
            atk_height=40,
            damage=30,
            atk_speed=0.1,
            atk_length=0.1,
            kb=(100, -80),
            modifiers=modifiers,
        )
