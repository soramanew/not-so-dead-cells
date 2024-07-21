import pygame
from item import Weapon
from util.func import clamp
from util.type import Colour, Size, Vec2

from .base import Panel, UIElement
from .text import Text


class ProgressBar(Panel):
    @property
    def max(self) -> float:
        return self._max

    @max.setter
    def max(self, value: float) -> None:
        if self._max == value:
            return

        self._max = value
        if self.progress_value:
            self.text.text_str = f"{int(self.value)}/{int(value)}"
        self.dirty = True

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        value = clamp(value, self.max, 0)

        if self._value == value:
            return

        self._value = value
        if self.progress_value:
            self.text.text_str = f"{int(value)}/{int(self.max)}"
        self.dirty = True

    @property
    def fill_colour(self) -> Colour:
        return self._fill_colour

    @fill_colour.setter
    def fill_colour(self, value: Colour) -> None:
        if self._fill_colour == value:
            return

        self._fill_colour = value
        self.dirty = True

    @property
    def background_colour(self) -> Colour:
        return self._background_colour

    @background_colour.setter
    def background_colour(self, value: Colour) -> None:
        if self._background_colour == value:
            return

        self._background_colour = value
        self.dirty = True

    @property
    def border_colour(self) -> Colour:
        return self._border_colour

    @border_colour.setter
    def border_colour(self, value: Colour) -> None:
        if self._border_colour == value:
            return

        self._border_colour = value
        self.dirty = True

    @property
    def border_thickness(self) -> float:
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value: float) -> None:
        if self._border_thickness == value:
            return

        self._border_thickness = value
        self.dirty = True

    @property
    def border_radius(self) -> float:
        return self._border_radius

    @border_radius.setter
    def border_radius(self, value: float) -> None:
        if self._border_radius == value:
            return

        self._border_radius = value
        self.dirty = True

    def __init__(
        self,
        relative_pos: Vec2,
        size: Size,
        maximum: float,
        fill_colour: Colour,
        progress_value: bool = False,  # Text showing progress value
        font: pygame.Font = None,
        background_colour: Colour = None,
        text_colour: Colour = (255, 255, 255),
        border_colour: Colour = None,
        border_thickness: int = 1,
        border_radius: int = 0,
        value: float = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.children: list[Text] = []

        self._max: float = maximum
        self._value: float = value

        self._fill_colour: Colour = fill_colour
        self._background_colour: Colour | None = background_colour

        self._border_colour: Colour | None = border_colour
        self._border_thickness: float = border_thickness
        self._border_radius: float = border_radius

        self.progress_value: bool = progress_value
        if progress_value:
            self.text: Text = Text(
                (0, 0), font, f"{int(value)}/{int(maximum)}", text_colour, container=self, anchors={"center": "center"}
            )

        self.surface: pygame.Surface = None

        super().__init__(relative_pos, size, container=container, anchors=anchors)

    def pack(self, recursion_depth: int = 0) -> None:
        pass  # Cannot be packed cause technically not a container

    def scale_by_ip(self, x: float, y: float = None) -> None:
        if y is None:
            y = x

        super().scale_by_ip(x, y)

        self.border_thickness *= x
        self.border_radius *= x

    def update(self) -> None:
        if self.dirty:
            self.surface = pygame.Surface(self.size, pygame.SRCALPHA).convert_alpha()
            rect = 0, 0, *self.size

            # Background
            radius = int(self.border_radius)
            if self.background_colour is not None:
                pygame.draw.rect(self.surface, self.background_colour, rect, border_radius=radius)

            # Filling
            filling = pygame.Surface((self.width * (self.value / self.max), self.height), pygame.SRCALPHA)
            pygame.draw.rect(filling, self.fill_colour, rect, border_radius=radius)
            self.surface.blit(filling, rect)  # In between surface to cut off end of rounded rect

            # Border
            if self.border_colour is not None:
                pygame.draw.rect(
                    self.surface, self.border_colour, rect, width=int(self.border_thickness), border_radius=radius
                )

        # Update text
        super().update()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.surface, self)

        # Draw text
        super().draw(surface)


class StackedProgressBar(Panel):
    @property
    def max(self) -> float:
        return self.children[0].max  # All children max should be the same

    @max.setter
    def max(self, value: float) -> None:
        for child in self.children:
            child.max = value

    @property
    def values(self) -> list[float]:
        return [self.get_value(i) for i in range(len(self.children))]

    @values.setter
    def values(self, value: list[float]) -> None:
        for i in range(len(value) - 1, -1, -1):
            self.set_value(value[i], i)

    @property
    def fill_colours(self) -> list[Colour]:
        return [child.fill_colour for child in self.children]

    @fill_colours.setter
    def fill_colours(self, value: list[Colour]) -> None:
        for i, v in enumerate(value):
            self.children[i].fill_colour = v

    @property
    def background_colour(self) -> Colour:
        return self.children[0].background_colour

    @background_colour.setter
    def background_colour(self, value: Colour) -> None:
        self.children[0].background_colour = value

    def __init__(
        self,
        relative_pos: Vec2,
        size: Size,
        maximum: float,
        fill_colours: list[Colour],
        layers: int,
        progress_value: bool = False,  # Text showing progress value
        font: pygame.Font = None,
        background_colour: Colour = None,
        text_colour: Colour = (255, 255, 255),
        border_colour: Colour = None,
        border_thickness: int = 1,
        border_radius: int = 0,
        values: list[float] = None,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.children: list[ProgressBar] = []

        values = values or [0] * layers

        def create_layer(colour, **kwargs):
            ProgressBar(
                (0, 0),
                size,
                maximum,
                colour,
                border_radius=border_radius,
                container=self,
                **kwargs,
            )

        # Base
        create_layer(fill_colours[0], background_colour=background_colour)

        # In between
        for i in range(1, layers - 1):  # 1 to layers - 2
            create_layer(fill_colours[i])

        # Last and topmost one
        create_layer(
            fill_colours[layers - 1],
            progress_value=progress_value,
            font=font,
            text_colour=text_colour,
            border_colour=border_colour,
            border_thickness=border_thickness,
        )

        for i in range(layers - 1, -1, -1):
            self.set_value(values[i], i)

        super().__init__(relative_pos, size, container=container, anchors=anchors)

    def pack(self, recursion_depth: int = 0) -> None:
        pass  # Cannot be packed cause technically not a container

    def get_value(self, layer: int) -> float:
        # Value is value - above layer values
        return self.children[layer].value - sum(ch.value for ch in self.children[layer + 1 :])

    def set_value(self, value: float, layer: int) -> None:
        # Value is value + above layer values
        self.children[layer].value = value + sum(ch.value for ch in self.children[layer + 1 :])


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
