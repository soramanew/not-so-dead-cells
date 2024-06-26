from random import uniform

import pygame
from box import Hitbox
from map import Map, Wall
from player import Player
from util.type import Interactable, Vec2

from item import Item


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
        # TODO draw item sprite and popup

    # def draw_popup(self, ui: pygame_gui.UIManager):
    #     # FIXME maybe just draw rect + text not use pygame_gui

    #     from item import Skill  # ARRGGHHH I HATE CIRCULAR IMPORTS

    #     pygame_gui.elements.UITextBox(
    #         f"<b><font face='Gabarito' size=20>{self.item.name}</font></b><br>"
    #         f"<font face='Rubik' size=14>{round(self.item.dps)} DPS{f" ({self.item.cooldown} sec)" if isinstance(self.item, Skill) else ""}</font>"
    #         "<hr>"
    #         f"<font face='Rubik' size=14>{self.item.modifiers_str}</font>",
    #         manager=ui,
    #     )

    def draw(self, surface: pygame.Surface, **kwargs) -> None:
        super().draw(surface, (74, 218, 192), **kwargs)


class WeaponPickup(Pickup):
    def interact(self, player: Player) -> None:
        player.switch_weapon(self.item)
        # self.map.remove(self)
