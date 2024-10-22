import logging
import math
from abc import abstractmethod
from random import random, uniform

import pygame
import state
from box import Hitbox
from map import Map, Wall
from util.func import (
    get_font,
    get_project_root,
    normalise_for_drawing,
    render_interact_text,
)
from util.type import Direction, Interactable, Sound, Vec2

from item import Item

FLOAT_MAX: float = 0.1

logger = logging.getLogger(__name__)


def _draw_popup_base(surface: pygame.Surface) -> None:
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
        sfx: str,
        platform_or_pos: Wall | Vec2,
        vx: float = None,
        vy: float = None,
    ):
        self.sprite: pygame.Surface = pygame.image.load(
            get_project_root() / "assets/sprites" / f"{sprite}.png"
        ).convert_alpha()
        width, height = self.sprite.size

        self.sunburst: pygame.Surface = pygame.image.load(
            get_project_root() / "assets/vfx/Sunburst.png"
        ).convert_alpha()
        # Scale to slightly larger than sprite
        self.sunburst = pygame.transform.scale(self.sunburst, (width * 1.5, height * 1.5))
        # Tint by sprite colour
        self.sunburst.fill((*pygame.transform.average_color(self.sprite)[:3], 255), special_flags=pygame.BLEND_ADD)

        self.sfx: Sound = Sound(get_project_root() / f"assets/sfx/interact/{sfx}")

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
            # Make center pos
            x -= width / 2
            y -= height / 2

        if vx is None:
            vx = uniform(5, 80) * (1 if random() < 0.5 else -1)
        if vy is None:
            vy = -uniform(100, 400)

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
        collisions = self.move(self.vx * dt, self.vy * dt)
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
        super().__init__(item.sprite, "Weapon.wav", platform_or_pos, vx, vy)
        item.sprite_img = self.sprite

    def _create_popup(self) -> pygame.Surface:
        if self.item.popup:
            return self.item.popup

        title_font = get_font("BIT", 20)
        text_font = get_font("Silkscreen", 16)

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

        _draw_popup_base(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(dps, (x_off, y_off))
        y_off += dps.height
        surface.blit(desc, (x_off, y_off))
        surface.blit(mods, (x_off, y_off + desc.height))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        self.item.popup = surface

        return surface

    def interact(self) -> None:
        state.player.switch_weapon(self.item)
        state.current_map.remove_pickup(self)
        self.sfx.play()


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
        super().__init__(f"food/{sprite}", "Food.wav", platform_or_pos, vx, vy)

    def _create_popup(self) -> pygame.Surface:
        title_font = get_font("BIT", 20)
        text_font = get_font("Silkscreen", 16)

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

        _draw_popup_base(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(effect, (x_off, y_off))
        surface.blit(desc, (x_off, y_off + effect.height))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        return surface

    def interact(self) -> None:
        state.player.heal(self.heal)
        state.current_map.remove_pickup(self)
        self.sfx.play()


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

        title_font = get_font("BIT", 20)
        text_font = get_font("Silkscreen", 16)
        unicode_font = get_font("NotoSans", 16)

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

        _draw_popup_base(surface)

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


class Potion(Pickup):
    def __init__(
        self,
        pot_type: str,
        desc: str,
        amount: float,
        platform_or_pos: Wall | Vec2,
        vx: float = None,
        vy: float = None,
    ):
        self.type: str = pot_type
        self.desc: str = desc
        effectiveness = random() + 0.5
        self.amount: float = amount * effectiveness
        self.size: str = (
            "Small" if effectiveness < 0.5 + 1 / 3 else ("Medium" if effectiveness < 0.5 + 2 / 3 else "Large")
        )
        super().__init__(
            f"potions/{pot_type.lower()}_{self.size.lower()}",
            "Potion.wav",
            platform_or_pos,
            vx,
            vy,
        )

    def _create_popup(self) -> pygame.Surface:
        title_font = get_font("BIT", 20)
        text_font = get_font("Silkscreen", 16)

        x_off = 15
        y_off = 15

        name = title_font.render(f"{self.size} Potion of {self.type}", True, (214, 202, 178))
        effect = text_font.render(
            f"Increases {self.type.lower()} by {round(self.amount)}% (multiplicative)", True, (220, 220, 220)
        )
        desc = text_font.render(self.desc, True, (255, 255, 255))
        prompt = render_interact_text("Drink")

        surface = pygame.Surface(
            (
                max(name.width, effect.width, desc.width, prompt.width) + x_off * 2,
                name.height + effect.height + desc.height + prompt.height + y_off * 2,
            ),
            pygame.SRCALPHA,
        ).convert_alpha()

        _draw_popup_base(surface)

        surface.blit(name, (x_off, y_off))
        y_off += name.height
        surface.blit(effect, (x_off, y_off))
        surface.blit(desc, (x_off, y_off + effect.height))
        surface.blit(prompt, ((surface.width - prompt.width) / 2, surface.height - prompt.height - 12))

        return surface


class DamagePotion(Potion):
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
        state.player.damage_potions += 1
        state.player.damage_mul *= 1 + self.amount / 100
        logger.debug(
            f"Picked up damage potion: {state.player.damage_potions} potions - {round(state.player.damage_mul * 100)}%"
        )
        state.current_map.remove_pickup(self)
        self.sfx.play()


class HealthPotion(Potion):
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
        state.player.health_potions += 1
        state.player.health_mul *= 1 + self.amount / 100
        logger.debug(
            f"Picked up health potion: {state.player.health_potions} potions - {round(state.player.health_mul * 100)}%"
        )
        state.current_map.remove_pickup(self)
        self.sfx.play()
