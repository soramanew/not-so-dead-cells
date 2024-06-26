from random import uniform

import pygame
from box import Hitbox
from map import Map, Wall
from player import Player
from util.func import normalise_for_drawing
from util.type import Interactable, Vec2

from item import Item

TITLE_FONT: pygame.font.SysFont = pygame.font.SysFont("Gabarito", 20, bold=True)
TEXT_FONT: pygame.font.SysFont = pygame.font.SysFont("Rubik", 16)


class Pickup(Hitbox, Interactable):
    def __init__(
        self,
        current_map: Map,
        item: Item,
        platform_or_pos: Wall | Vec2,
        width: int = 30,
        height: int = 30,
    ):
        if isinstance(platform_or_pos, Wall):
            # Platform
            while True:
                x = uniform(platform_or_pos.left, platform_or_pos.right - width)
                y = platform_or_pos.top - height
                # Check for collisions
                if not current_map.get_rect(
                    x, y, width, height, lambda o: o is not platform_or_pos and isinstance(o, Wall)
                ):
                    break
        else:
            # Position
            x, y = platform_or_pos

        super().__init__(x, y, width, height)
        self.map: Map = current_map
        self.item: Item = item

        from item import Skill  # ARRGGHHH I HATE CIRCULAR IMPORTS

        x_off = 10
        y_off = 10
        name = TITLE_FONT.render(self.item.name, True, (214, 202, 178))
        dps = TEXT_FONT.render(
            f"{self.item.dps} DPS{f" ({self.item.cooldown} sec)" if isinstance(self.item, Skill) else ""}",
            True,
            (220, 220, 220),
        )
        desc = TEXT_FONT.render(self.item.desc, True, (255, 255, 255))
        mods = TEXT_FONT.render(self.item.modifiers_str, True, (200, 181, 143))
        self.surface: pygame.Surface = pygame.Surface(
            (
                max(name.width, dps.width, desc.width, mods.width) + x_off * 2,
                name.height + dps.height + desc.height + mods.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        )
        self.surface.fill((152, 138, 112, 230))
        self.surface.blit(name, (x_off, y_off))
        y_off += name.height
        self.surface.blit(dps, (x_off, y_off))
        y_off += dps.height
        self.surface.blit(desc, (x_off, y_off))
        y_off += desc.height
        self.surface.blit(mods, (x_off, y_off))
        # TODO draw item sprite and popup

    def draw_popup(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0, **kwargs) -> None:
        x, y, _w, _h = normalise_for_drawing(
            self.center_x - self.surface.width / 2,
            self.y - self.surface.height - 20,
            self.surface.width,
            self.surface.height,
            x_off,
            y_off,
        )
        surface.blit(self.surface, (x, y))

    def draw(self, surface: pygame.Surface, **kwargs) -> None:
        super().draw(surface, (74, 218, 192), **kwargs)


class WeaponPickup(Pickup):
    def interact(self, player: Player) -> None:
        player.switch_weapon(self.item)
        # self.map.remove(self)
