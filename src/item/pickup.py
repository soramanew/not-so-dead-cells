import math
from abc import abstractmethod
from random import random, uniform

import pygame
import state
from box import Hitbox
from map import Map, Wall
from util.func import get_project_root, normalise_for_drawing, render_interact_text
from util.type import Direction, Interactable, Vec2

from item import Item

FLOAT_MAX: float = 0.1


def _draw_border(surface: pygame.Surface) -> None:
    pygame.draw.rect(surface, (152, 138, 112, 230), (0, 0, surface.width, surface.height), border_radius=3)
    pygame.draw.rect(surface, (210, 193, 158), (0, 0, surface.width, surface.height), width=1, border_radius=3)


class Pickup(Hitbox, Interactable):
    @abstractmethod
    def _create_popup(self) -> pygame.Surface:
        pass

    @property
    def anim_offset(self) -> Vec2:
        return self.height * math.sin(self.time * math.pi) * self.float_speed * FLOAT_MAX

    def __init__(
        self,
        sprite: str,
        platform_or_pos: Wall | Vec2,
        vx: float = None,
        vy: float = None,
    ):
        self.sprite: pygame.Surface = pygame.image.load(
            get_project_root() / "assets/sprites" / f"{sprite}.png"
        ).convert_alpha()
        width, height = self.sprite.size

        self.sunburst: pygame.Surface = pygame.image.load(
            get_project_root() / "assets/sprites/sunburst.png"
        ).convert_alpha()
        # Scale to slightly larger than sprite
        self.sunburst = pygame.transform.scale(self.sunburst, (width * 1.5, height * 1.5))
        # Tint by sprite colour
        self.sunburst.fill((*pygame.transform.average_color(self.sprite)[:3], 255), special_flags=pygame.BLEND_ADD)

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

        self.rot_speed: float = uniform(0.5, 1.5) * (1 if random() < 0.5 else -1)
        self.float_speed: float = uniform(0.5, 1.5)
        self.time: float = 0

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

        if self.vx == 0 and self.vy == 0:
            self.time += dt

    def draw_popup(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0, **kwargs) -> None:
        x, y, _w, _h = normalise_for_drawing(
            self.center_x - self.surface.width / 2,
            self.y - self.surface.height - 20 - self.anim_offset,
            self.surface.width,
            self.surface.height,
            x_off,
            y_off,
        )
        surface.blit(self.surface, (x, y))

    def draw(self, surface: pygame.Surface, x_off: float = 0, y_off: float = 0, **kwargs) -> None:
        # super().draw(surface, (74, 218, 192), x_off, y_off, **kwargs)

        # Rotate sunburst
        sunburst = pygame.transform.rotate(self.sunburst, self.time * self.rot_speed * 10)
        new_rect = sunburst.get_rect(
            center=self.sunburst.get_rect(
                topleft=(
                    self.center_x - self.sunburst.width / 2 + x_off,
                    self.center_y - self.sunburst.height / 2 + y_off - self.anim_offset,
                )
            ).center
        )
        # Draw sunburst
        surface.blit(sunburst, new_rect)

        # Actually draw sprite
        surface.blit(self.sprite, (self.x + x_off, self.y - self.anim_offset + y_off))


class WeaponPickup(Pickup):
    def __init__(self, item: Item, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        self.item: Item = item
        super().__init__(item.sprite, platform_or_pos, vx, vy)

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
        sprite: str,
        platform_or_pos: Wall | Vec2,
        vx: float = None,
        vy: float = None,
    ):
        self.name: str = name
        self.desc: str = desc
        self.heal: int = int(heal * state.difficulty * 0.6)  # Player health & healing scales much slower
        super().__init__(sprite, platform_or_pos, vx, vy)

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
    def __init__(self, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        super().__init__(
            "Mouldy Apple",
            "I really don't think you should eat this, but you have a tough stomach right?",
            10,
            "apple",
            platform_or_pos,
            vx,
            vy,
        )


class Toe(Food):
    def __init__(self, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        super().__init__(
            "Mutilated Toe",
            "You know, I heard witches make pretty good stews with these...",
            20,
            "toe",
            platform_or_pos,
            vx,
            vy,
        )


class LemonPie(Food):
    def __init__(self, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        super().__init__(
            "Half-eaten Lemon Pie",
            "Who threw this away? I hope they didn't have herpes...",
            30,
            "lemon_pie",
            platform_or_pos,
            vx,
            vy,
        )


class Sausages(Food):
    def __init__(self, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        super().__init__(
            "Mystery Sausages",
            "",  # Desc overridden
            50,
            "sausages",
            platform_or_pos,
            vx,
            vy,
        )

    def _create_popup(self) -> pygame.Surface:
        """Pygame doesn't support fallback fonts so I have to make this special."""

        title_font = pygame.font.SysFont("Gabarito", 20, bold=True)
        text_font = pygame.font.SysFont("Rubik", 16)
        unicode_font = pygame.font.SysFont("Noto Sans", 16)

        x_off = 15
        y_off = 15

        name = title_font.render(self.name, True, (214, 202, 178))
        effect = text_font.render(f"Heals {self.heal}HP", True, (220, 220, 220))
        desc1 = text_font.render("These look more like ", True, (255, 255, 255))
        desc2 = unicode_font.render("s̵̡̧̠̫͚̪͙̜̗͓̎̇̅̅̃͛̿h̸̢͎͚̱̪̝̠̟̟̱͕͚͔͗̂̄ͅî̷̱̝͖̣̲͚͎̘̒͗̕t̶̝̖͔̙̲͍̻̝͓͙̎̒̔", True, (255, 255, 255))
        desc3 = text_font.render(" than sausages.", True, (255, 255, 255))
        prompt = render_interact_text("Eat")

        surface = pygame.Surface(
            (
                max(name.width, effect.width, desc1.width + desc2.width + desc3.width, prompt.width) + x_off * 2,
                name.height + effect.height + max(desc1.height, desc3.height) + prompt.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        ).convert_alpha()

        _draw_border(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(effect, (x_off, y_off))
        y_off += effect.height
        surface.blit(desc1, (x_off, y_off))
        x_off += desc1.width
        surface.blit(desc2, (x_off, y_off - desc2.height / 2))
        surface.blit(desc3, (x_off + desc2.width, y_off))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        return surface


class Scroll(Pickup):
    def __init__(
        self,
        scroll_type: str,
        desc: str,
        amount: float,
        platform_or_pos: Wall | Vec2,
        vx: float = None,
        vy: float = None,
    ):
        self.type: str = scroll_type
        self.desc: str = desc
        self.amount: float = amount * (random() + 0.5)
        super().__init__(f"{scroll_type.lower()}_scroll", platform_or_pos, vx, vy)

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
    def __init__(self, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        super().__init__(
            "Damage",
            "Turns even the fluffiest bunny into a rage-fueled killing machine (batteries not included).",
            10,
            platform_or_pos,
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
    def __init__(self, platform_or_pos: Wall | Vec2, vx: float = None, vy: float = None):
        super().__init__(
            "Health",
            "Instantly transforms you from a soft marshmallow to a slightly firmer marshmallow.",
            10,
            platform_or_pos,
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
