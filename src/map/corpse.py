from random import choice, random, uniform

import pygame
import state
from box import Box
from util.func import get_project_root, render_interact_text
from util.type import Interactable, Sound

from .wall import Wall


def _create_popup(text: str, key: bool = True) -> pygame.Surface:
    text = render_interact_text(text, key=key)
    margin_x = 5
    margin_y = 4
    surface = pygame.Surface((text.width + margin_x * 2, text.height + margin_y * 2), pygame.SRCALPHA).convert_alpha()
    pygame.draw.rect(surface, (152, 138, 112, 230), (0, 0, surface.width, surface.height), border_radius=3)
    pygame.draw.rect(surface, (210, 193, 158), (0, 0, surface.width, surface.height), width=1, border_radius=3)
    surface.blit(text, (margin_x, margin_y))
    return surface


class Corpse(Box, Interactable):
    def __init__(self, platform: Wall):
        sprite = pygame.image.load(
            choice([f for f in (get_project_root() / "assets/sprites/corpses").iterdir() if f.is_file()])
        )
        sprite_rect = sprite.get_bounding_rect()
        width, height = sprite_rect.size
        self.sprite: pygame.Surface = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
        self.sprite.blit(sprite, (0, 0), sprite_rect)

        while True:
            x = uniform(platform.left, platform.right - width)
            y = platform.top - height
            # Check for collisions
            if not state.current_map.get_rect(x, y, width, height, lambda o: o is not platform and isinstance(o, Wall)):
                break

        super().__init__(x, y, width, height)
        self.popup: pygame.Surface = _create_popup("Inspect")
        self.looted: bool = False
        self.sfx: Sound = Sound(get_project_root() / "assets/sfx/interact/Corpse.wav")

    def interact(self) -> None:
        if self.looted:
            return

        self.sfx.play(maxtime=1000)

        self.looted = True
        if random() < 0.5:
            state.current_map.spawn_weapon(self.center_x, self.y - 30)
            self.popup = None
        else:
            self.popup = _create_popup("Womp Womp", key=False)

    def draw_popup(self, surface: pygame.Surface, x_off: float, y_off: float, **kwargs) -> None:
        if self.popup is not None:
            surface.blit(
                self.popup,
                (self.center_x + x_off - self.popup.width / 2, self.y - self.height * 0.1 - self.popup.height + y_off),
            )

    def draw(
        self,
        surface: pygame.Surface,
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        # super().draw(surface, (53, 43, 243), x_off, y_off, scale)
        surface.blit(self.sprite, (self.x + x_off, self.y + y_off))
