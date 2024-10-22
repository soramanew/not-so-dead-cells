import logging

import pygame
import state
from box import Box
from util.func import get_project_root, render_interact_text
from util.type import Interactable, Sound

logger = logging.getLogger(__name__)


def _create_popup() -> pygame.Surface:
    text = render_interact_text("Enter")
    margin_x = 5
    margin_y = 4
    surface = pygame.Surface((text.width + margin_x * 2, text.height + margin_y * 2), pygame.SRCALPHA).convert_alpha()
    pygame.draw.rect(surface, (152, 138, 112, 230), (0, 0, surface.width, surface.height), border_radius=3)
    pygame.draw.rect(surface, (210, 193, 158), (0, 0, surface.width, surface.height), width=1, border_radius=3)
    surface.blit(text, (margin_x, margin_y))
    return surface


class Gate(Box, Interactable):
    def __init__(self, x: float, y: float, width: int, height: int):
        super().__init__(x, y, width, height)
        self.popup: pygame.Surface = _create_popup()
        self.sfx: Sound = Sound(get_project_root() / "assets/sfx/interact/Gate.wav")

    def interact(self) -> None:
        from map import Map  # Damn you circular imports

        self.sfx.play()
        diff = round(state.difficulty, 2)
        state.difficulty *= 1.3
        logger.info(f"Difficulty {diff} -> {round(state.difficulty, 2)}")
        state.current_map = Map()
        state.map_loaded = False

    def draw_popup(self, surface: pygame.Surface, x_off: float, y_off: float, **kwargs) -> None:
        surface.blit(self.popup, (self.center_x + x_off - self.popup.width / 2, self.y + self.height * 0.4 + y_off))

    def draw(
        self,
        surface: pygame.Surface,
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        # super().draw(surface, (94, 66, 195), x_off, y_off, scale)
        pass  # Ignore, part of texture
