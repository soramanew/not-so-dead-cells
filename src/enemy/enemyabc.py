from abc import abstractmethod

from box import BoxABC
from map import Map, Wall
from util.type import Side


class EnemyABC(BoxABC):
    map: Map
    platform: Wall
    facing: Side
    alerted: bool
    atk_range: float

    @property
    @abstractmethod
    def head_x(self) -> float:
        pass

    @property
    @abstractmethod
    def head_y(self) -> float:
        pass

    @abstractmethod
    def _get_dep_facing(self, ratio: float) -> float:
        pass
