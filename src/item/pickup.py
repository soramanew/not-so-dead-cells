from random import random, uniform

import pygame
from box import Hitbox
from map import Map, Wall
from player import Player
from util.func import normalise_for_drawing
from util.type import Direction, Interactable, Vec2

from item import Item

TITLE_FONT: pygame.font.SysFont = pygame.font.SysFont("Gabarito", 20, bold=True)
TEXT_FONT: pygame.font.SysFont = pygame.font.SysFont("Rubik", 16)
PROMPT = pygame.font.SysFont("Readex Pro", 16).render("[F] to pick up", True, (255, 255, 255))


class Pickup(Hitbox, Interactable):
    def __init__(
        self,
        current_map: Map,
        item: Item,
        platform_or_pos: Wall | Vec2,
        width: int = 30,
        height: int = 30,
        vx: float = None,
        vy: float = None,
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

        if vx is None:
            vx = uniform(5, 20) * (1 if random() < 0.5 else -1)
        if vy is None:
            vy = -uniform(100, 200)

        super().__init__(x, y, width, height)
        self.map: Map = current_map
        self.item: Item = item
        self.vx: float = vx
        self.vy: float = vy

        from item import Skill  # ARRGGHHH I HATE CIRCULAR IMPORTS

        x_off = 15
        y_off = 15
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
                max(name.width, dps.width, desc.width, mods.width, PROMPT.width) + x_off * 2,
                name.height + dps.height + desc.height + mods.height + PROMPT.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        )
        pygame.draw.rect(
            self.surface, (152, 138, 112, 230), (0, 0, self.surface.width, self.surface.height), border_radius=3
        )
        pygame.draw.rect(
            self.surface,
            (210, 193, 158),
            (0, 0, self.surface.width, self.surface.height),
            width=1,
            border_radius=3,
        )
        self.surface.blit(name, (x_off, y_off))
        y_off += name.height
        self.surface.blit(dps, (x_off, y_off))
        y_off += dps.height
        self.surface.blit(desc, (x_off, y_off))
        y_off += desc.height
        self.surface.blit(mods, (x_off, y_off))
        self.surface.blit(PROMPT, ((self.surface.width - PROMPT.width) / 2, self.surface.height - PROMPT.height - 12))

    def tick(self, dt: float) -> None:
        self.vx -= Map.get_air_resistance(self.vx, self.height) * dt
        self.vy += (Map.GRAVITY - Map.get_air_resistance(self.vy, self.width)) * dt
        collisions = self.move(self.vx * dt, self.vy * dt, self.map.walls)
        for direction, entity in collisions:
            if direction is Direction.DOWN and isinstance(entity, Wall):
                self.vx = 0
                self.vy = 0
                break

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
        self.map.remove_pickup(self)
