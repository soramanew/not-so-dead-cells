from util.type import Side

from ..melee import MeleeWeapon


class Sword(MeleeWeapon):
    @MeleeWeapon.left.getter
    def left(self) -> float:
        return self.player.left - self.width if self.player.facing is Side.LEFT else self.player.right

    @MeleeWeapon.top.getter
    def top(self) -> float:
        return self.atk_top + (self.atk_height - self.height) * ((self.atk_length - self.atk_time) / self.atk_length)
