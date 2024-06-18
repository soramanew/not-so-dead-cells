from util.type import Side

from ..melee import MeleeWeapon


class Sword(MeleeWeapon):
    @property
    def atk_top(self) -> float:
        return self.player.arm_y - self.height / 2

    @MeleeWeapon.left.getter
    def left(self) -> float:
        return self.player.left - self.height if self.player.facing is Side.LEFT else self.player.right

    @MeleeWeapon.top.getter
    def top(self) -> float:
        return self.atk_top + (self.atk_height - self.height) * ((self.atk_length - self.atk_time) / self.atk_length)
