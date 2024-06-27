from util.func import normalise_rect
from util.type import Rect, Side

from .melee import MeleeAttack


class DiagonalUpOut(MeleeAttack):
    @property
    def atk_top(self) -> float:
        return self.arm_y - self.atk_height / 2

    def __init__(self, atk_height: float, atk_height_tick: float, **kwargs):
        self.atk_height: float = atk_height
        self.atk_height_tick: float = atk_height_tick
        super().__init__(**kwargs)

    def _get_atk_area(self) -> Rect:
        return normalise_rect(
            self.front,
            self.atk_top,
            self.atk_width * (1 if self.facing is Side.RIGHT else -1),
            self.atk_height,
        )

    def _get_real_atk_area(self) -> Rect:
        return normalise_rect(
            self.front,
            self.atk_top + (self.atk_height - self.atk_height_tick) * (self.atk_time / self.atk_length),
            self.atk_width * (self.atk_time / self.atk_length) * (1 if self.facing is Side.RIGHT else -1),
            self.atk_height_tick,
        )
