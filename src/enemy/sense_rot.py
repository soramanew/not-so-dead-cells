from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .enemy import Movement

from box import RotatedBox
from util.type import Side


class EnemySense(RotatedBox):
    @property
    def anchor_x(self) -> float:
        return self.parent.head_x

    @anchor_x.setter
    def anchor_x(self, value):
        pass

    @property
    def anchor_y(self) -> float:
        return self.parent.head_y

    @anchor_y.setter
    def anchor_y(self, value):
        pass

    @property
    def anchor_xr(self) -> float:
        return self._anchor_xr if self.parent.facing is Side.RIGHT else 1 - self._anchor_xr

    @anchor_xr.setter
    def anchor_xr(self, value):
        pass

    def __init__(
        self,
        parent: Movement,
        width: int,
        height: int,
        angle: float,
        xray: bool = False,
        anchor_xr: float = 0,
        anchor_yr: float = 0.5,
    ):
        super().__init__(parent.head_x, parent.head_y, width, height, angle, anchor_yr=anchor_yr)

        self.parent: Movement = parent  # The Enemy this belongs to
        self.xray: bool = xray  # If the sense goes through walls
        self._anchor_xr: float = anchor_xr
        # TODO maybe just use rectangles no rotated
        # TODO use multiple inheritance

    def check_for_player(self):
        # TODO
        pass
