from abc import abstractmethod

from box import BoxABC
from map import Map, Wall
from player import Player
from util.type import Side


class EnemyABC(BoxABC):
    player: Player
    map: Map
    platform: Wall
    facing: Side
    atk_width: int
    atk_windup: float
    atk_speed: float
    atk_length: float
    health: int
    damage: int
    alerted: bool

    @property
    @abstractmethod
    def head_x(self) -> float:
        pass

    @property
    @abstractmethod
    def head_y(self) -> float:
        pass

    @property
    @abstractmethod
    def front(self) -> float:
        pass

    @property
    @abstractmethod
    def atk_stop_mv(self) -> bool:
        """If the enemy is stopped due to attacking."""
        pass

    @abstractmethod
    def _get_dep_facing(self, ratio: float) -> float:
        pass

    @abstractmethod
    def _tick_attack(self) -> None:
        pass
