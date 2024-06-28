from abc import abstractmethod
from random import random, uniform

import pygame
import state
from box import Hitbox
from map import Map, Wall
from util.func import normalise_for_drawing, render_interact_text
from util.type import Direction, Interactable, Vec2

from item import Item


def _draw_border(surface: pygame.Surface) -> None:
    pygame.draw.rect(surface, (152, 138, 112, 230), (0, 0, surface.width, surface.height), border_radius=3)
    pygame.draw.rect(surface, (210, 193, 158), (0, 0, surface.width, surface.height), width=1, border_radius=3)


class Pickup(Hitbox, Interactable):
    @abstractmethod
    def _create_popup(self) -> pygame.Surface:
        pass

    def __init__(
        self, platform_or_pos: Wall | Vec2, width: int = 30, height: int = 30, vx: float = None, vy: float = None
    ):
        if isinstance(platform_or_pos, Wall):
            # Platform
            while True:
                x = uniform(platform_or_pos.left, platform_or_pos.right - width)
                y = platform_or_pos.top - height
                # Check for collisions
                if not state.current_map.get_rect(
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
        self.vx: float = vx
        self.vy: float = vy

        self.surface: pygame.Surface = self._create_popup()

    def tick(self, dt: float) -> None:
        self.vx -= Map.get_air_resistance(self.vx, self.height) * dt
        self.vy += (Map.GRAVITY - Map.get_air_resistance(self.vy, self.width)) * dt
        collisions = self.move(self.vx * dt, self.vy * dt, state.current_map.walls)
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
    def __init__(
        self,
        item: Item,
        platform_or_pos: Wall | Vec2,
        width: int = 30,
        height: int = 30,
        vx: float = None,
        vy: float = None,
    ):
        self.item: Item = item
        super().__init__(platform_or_pos, width, height, vx, vy)

    def _create_popup(self) -> pygame.Surface:
        title_font = pygame.font.SysFont("Gabarito", 20, bold=True)
        text_font = pygame.font.SysFont("Rubik", 16)

        x_off = 15
        y_off = 15

        name = title_font.render(self.item.name, True, (214, 202, 178))
        dps = text_font.render(f"{self.item.dps} DPS", True, (220, 220, 220))
        desc = text_font.render(self.item.desc, True, (255, 255, 255))
        mods = text_font.render(self.item.modifiers_str, True, (200, 181, 143))
        prompt = render_interact_text("Pick Up")

        surface = pygame.Surface(
            (
                max(name.width, dps.width, desc.width, mods.width, prompt.width) + x_off * 2,
                name.height + dps.height + desc.height + mods.height + prompt.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        ).convert_alpha()

        _draw_border(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(dps, (x_off, y_off))
        y_off += dps.height
        surface.blit(desc, (x_off, y_off))
        surface.blit(mods, (x_off, y_off + desc.height))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        return surface

    def interact(self) -> None:
        state.player.switch_weapon(self.item)
        state.current_map.remove_pickup(self)


class Food(Pickup):
    def __init__(
        self,
        name: str,
        desc: str,
        heal: int,
        platform_or_pos: Wall | Vec2,
        width: int = 30,
        height: int = 30,
        vx: float = None,
        vy: float = None,
    ):
        self.name: str = name
        self.desc: str = desc
        self.heal: int = int(heal * state.difficulty * 0.6)  # Player health & healing scales much slower
        super().__init__(platform_or_pos, width, height, vx, vy)

    def _create_popup(self) -> pygame.Surface:
        title_font = pygame.font.SysFont("Gabarito", 20, bold=True)
        text_font = pygame.font.SysFont("Rubik", 16)

        x_off = 15
        y_off = 15

        name = title_font.render(self.name, True, (214, 202, 178))
        effect = text_font.render(f"Heals {self.heal}HP", True, (220, 220, 220))
        desc = text_font.render(self.desc, True, (255, 255, 255))
        prompt = render_interact_text("Eat")

        surface = pygame.Surface(
            (
                max(name.width, effect.width, desc.width, prompt.width) + x_off * 2,
                name.height + effect.height + desc.height + prompt.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        ).convert_alpha()

        _draw_border(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(effect, (x_off, y_off))
        surface.blit(desc, (x_off, y_off + effect.height))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        return surface

    def interact(self) -> None:
        state.player.heal(self.heal)
        state.current_map.remove_pickup(self)


class Apple(Food):
    def __init__(
        self, platform_or_pos: Wall | Vec2, width: int = 30, height: int = 30, vx: float = None, vy: float = None
    ):
        super().__init__(
            "Mouldy Apple",
            "I really don't think you should eat this, but you have a tough stomach right?",
            10,
            platform_or_pos,
            width,
            height,
            vx,
            vy,
        )


class Kebab(Food):
    def __init__(
        self, platform_or_pos: Wall | Vec2, width: int = 30, height: int = 30, vx: float = None, vy: float = None
    ):
        super().__init__(
            "Half-eaten Kebab",
            "Who threw this away? I hope they didn't have herpes...",
            30,
            platform_or_pos,
            width,
            height,
            vx,
            vy,
        )


class Meatloaf(Food):
    def __init__(
        self, platform_or_pos: Wall | Vec2, width: int = 30, height: int = 30, vx: float = None, vy: float = None
    ):
        super().__init__(
            "Slimy Meatloaf",
            "Is there really no good food around here?",
            50,
            platform_or_pos,
            width,
            height,
            vx,
            vy,
        )


class Scroll(Pickup):
    def __init__(
        self,
        scroll_type: str,
        desc: str,
        amount: float,
        platform_or_pos: Wall | Vec2,
        width: int = 30,
        height: int = 30,
        vx: float = None,
        vy: float = None,
    ):
        self.type: str = scroll_type
        self.desc: str = desc
        self.amount: float = amount * (random() + 0.5)
        super().__init__(platform_or_pos, width, height, vx, vy)

    def _create_popup(self) -> pygame.Surface:
        title_font = pygame.font.SysFont("Gabarito", 20, bold=True)
        text_font = pygame.font.SysFont("Rubik", 16)

        x_off = 15
        y_off = 15

        name = title_font.render(f"Scroll of {self.type}", True, (214, 202, 178))
        effect = text_font.render(
            f"Increases {self.type.lower()} by {round(self.amount)}% (multiplicative)", True, (220, 220, 220)
        )
        desc = text_font.render(self.desc, True, (255, 255, 255))
        prompt = render_interact_text("Read")

        surface = pygame.Surface(
            (
                max(name.width, effect.width, desc.width, prompt.width) + x_off * 2,
                name.height + effect.height + desc.height + prompt.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        ).convert_alpha()

        _draw_border(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(effect, (x_off, y_off))
        surface.blit(desc, (x_off, y_off + effect.height))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        return surface


class DamageScroll(Scroll):
    def __init__(
        self, platform_or_pos: Wall | Vec2, width: int = 30, height: int = 30, vx: float = None, vy: float = None
    ):
        super().__init__(
            "Damage",
            "Turns even the fluffiest bunny into a rage-fueled killing machine (batteries not included).",
            10,
            platform_or_pos,
            width,
            height,
            vx,
            vy,
        )

    def interact(self) -> None:
        state.player.damage_scrolls += 1
        state.player.damage_mul *= 1 + self.amount / 100
        print(
            f"[DEBUG] Picked up damage scroll: {state.player.damage_scrolls} scrolls - {round(state.player.damage_mul * 100)}%"
        )
        state.current_map.remove_pickup(self)


class HealthScroll(Scroll):
    def __init__(
        self, platform_or_pos: Wall | Vec2, width: int = 30, height: int = 30, vx: float = None, vy: float = None
    ):
        super().__init__(
            "Health",
            "Instantly transforms you from a soft marshmallow to a slightly firmer marshmallow.",
            10,
            platform_or_pos,
            width,
            height,
            vx,
            vy,
        )

    def interact(self) -> None:
        state.player.health_scrolls += 1
        state.player.health_mul *= 1 + self.amount / 100
        print(
            f"[DEBUG] Picked up health scroll: {state.player.health_scrolls} scrolls - {round(state.player.health_mul * 100)}%"
        )
        state.current_map.remove_pickup(self)
