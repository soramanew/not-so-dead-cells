import pygame
from player import Player
from util.type import Colour

from .enemyabc import EnemyABC


class Sense(EnemyABC):
    @property
    def sense_x(self) -> float:
        return self.head_x - self._get_dep_facing(self._sense_x) * self.sense_width

    @property
    def sense_y(self) -> float:
        return self.head_y - self._sense_y

    def __init__(self, sense_x: float, sense_y: float, sense_width: int, sense_height: int, **kwargs):
        super().__init__(**kwargs)
        self._sense_x: float = sense_x
        self._sense_y: float = sense_y * sense_height
        self.sense_width: int = sense_width
        self.sense_height: int = sense_height

    def check_for_player(self, player: Player) -> bool:
        return player.detect_collision_rect(self.sense_x, self.sense_y, self.sense_width, self.sense_height)

    def _tick_sense(self, player: Player) -> None:
        self.alerted = self.check_for_player(player)

    def draw_sense(
        self,
        surface: pygame.Surface,
        colours: tuple[Colour, Colour],
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        x = (self.sense_x + x_off) * scale
        y = (self.sense_y + y_off) * scale
        width = self.sense_width * scale
        height = self.sense_height * scale
        if x < 0:
            width += x
            x = 0
        if y < 0:
            height += y
            y = 0
        if width < 0 or height < 0:
            return
        s = pygame.Surface((width, height))
        s.set_alpha(128)
        s.fill(colours[1 if self.alerted else 0])
        surface.blit(s, (x, y))
