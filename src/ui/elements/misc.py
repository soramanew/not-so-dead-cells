import pygame
from item import Weapon
from util.type import Colour, Size, Vec2

from .base import Panel, UIElement
from .text import Text


class Image(UIElement):
    @property
    def image(self) -> pygame.Surface:
        return self.scaled

    @image.setter
    def image(self, value: pygame.Surface) -> None:
        if self.original == value:
            return

        self.original = value
        self.scaled = pygame.transform.scale_by(value, (self.width / value.width, self.height / value.height))
        self.dirty = True

    def __init__(
        self,
        relative_pos: Vec2,
        image: pygame.Surface,
        size: Size = None,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.original: pygame.Surface = image
        self.scaled: pygame.Surface = image

        super().__init__(relative_pos, image.size, container=container, anchors=anchors)

        if size:
            self.scale_by_ip(size[0] / self.width, size[1] / self.height)

    def scale_by_ip(self, x: float, y: float = None) -> None:
        if y is None:
            y = x

        super().scale_by_ip(x, y)

        self.scaled = pygame.transform.scale_by(
            self.original, (self.width / self.original.width, self.height / self.original.height)
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.scaled, self)


class WeaponDisplay(Panel):
    @property
    def weapon(self) -> Weapon:
        return self._weapon

    @weapon.setter
    def weapon(self, value: Weapon) -> None:
        if self._weapon == value:
            return

        self._weapon = value
        self.image.image = value.sprite_img
        self.name.text_str = value.name
        self.dps.text_str = f"{value.dps} DPS"
        self.modifiers.text_str = value.modifiers_str
        self.image.scale_by_ip((self.dps.bottom - self.name.top) / self.image.height)

        self.dirty = True

    def __init__(
        self,
        relative_pos: Vec2,
        weapon: Weapon,
        name_font: pygame.Font,
        dps_font: pygame.Font,
        mods_font: pygame.Font,
        name_colour: Colour = (255, 255, 255),
        dps_colour: Colour = (255, 255, 255),
        mods_colour: Colour = (255, 255, 255),
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self._weapon: Weapon = weapon

        self.children: list[Text] = []

        self.image: Image = Image((0, 0), weapon.sprite_img, container=self)
        self.name: Text = Text(
            (10, 0),
            name_font,
            weapon.name,
            name_colour,
            container=self,
            anchors={"left": "right", "left_target": self.image},
        )
        self.dps: Text = Text(
            (10, 10),
            dps_font,
            f"{weapon.dps} DPS",
            dps_colour,
            container=self,
            anchors={"left": "right", "left_target": self.image, "top": "bottom", "top_target": self.name},
        )
        self.modifiers: Text = Text(
            (10, 20),
            mods_font,
            weapon.modifiers_str,
            mods_colour,
            container=self,
            anchors={"top": "bottom", "top_target": self.dps},
        )

        # Scale to fit height
        self.image.scale_by_ip((self.dps.bottom - self.name.top) / self.image.height)

        super().__init__(relative_pos, container=container, anchors=anchors)
