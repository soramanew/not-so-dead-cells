from abc import ABC, abstractmethod
from typing import Callable

import pygame
from util.func import clamp
from util.type import Colour, Size, Vec2

from .base import Panel, UIElement
from .text import Text


class _ProgressBarABC(ABC, Panel):
    @property
    @abstractmethod
    def value(self) -> float:
        pass

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

    @property
    def gaps(self) -> float:
        return self._gaps

    @gaps.setter
    def gaps(self, value: float) -> None:
        if self._gaps == value:
            return

        self._gaps = value
        self.dirty = True

    def __init__(
        self,
        relative_pos: Vec2,
        size: Size,
        maximum: float,
        progress_value: bool = False,  # Text showing progress value
        font: pygame.Font = None,
        background_colour: Colour = None,
        text_colour: Colour = (255, 255, 255),
        border_colour: Colour = None,
        border_thickness: int = 1,
        border_radius: int = 0,
        gaps: Vec2 = (0, 0),
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.children: list[Text] = []

        self._max: float = maximum

        self._background_colour: Colour | None = background_colour

        self._border_colour: Colour | None = border_colour
        self._border_thickness: float = border_thickness
        self._border_radius: float = border_radius

        self._gaps: Vec2 = gaps

        self.progress_value: bool = progress_value
        if progress_value:
            self.text: Text = Text(
                (0, 0),
                font,
                f"{int(self.value)}/{int(maximum)}",
                text_colour,
                container=self,
                anchors={"center": "center"},
            )

        self.surface: pygame.Surface = None

        super().__init__(relative_pos, size=size, container=container, anchors=anchors)

    def pack(self, recursion_depth: int = 0) -> None:
        pass  # Cannot be packed cause technically not a container

    def scale_by_ip(self, x: float, y: float = None) -> None:
        if y is None:
            y = x

        super().scale_by_ip(x, y)

        self.border_thickness *= x
        self.border_radius *= x

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.surface, self)

        # Draw text
        super().draw(surface)


class ProgressBar(_ProgressBarABC):
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
        gaps: Vec2 = (0, 0),
        value: float = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self._value: float = value
        self._fill_colour: Colour = fill_colour

        super().__init__(
            relative_pos,
            size,
            maximum,
            progress_value=progress_value,
            font=font,
            background_colour=background_colour,
            text_colour=text_colour,
            border_colour=border_colour,
            border_thickness=border_thickness,
            border_radius=border_radius,
            gaps=gaps,
            container=container,
            anchors=anchors,
        )

    def update(self) -> None:
        if self.dirty:
            self.surface = pygame.Surface(self.size, pygame.SRCALPHA).convert_alpha()
            rect = 0, 0, *self.size

            # Background
            radius = int(self.border_radius)
            if self.background_colour is not None:
                pygame.draw.rect(self.surface, self.background_colour, rect, border_radius=radius)

            # Filling
            width = self.width - self.gaps[0] * 2
            height = self.height - self.gaps[1] * 2
            filling = pygame.Surface((width * (self.value / self.max), height), pygame.SRCALPHA)
            pygame.draw.rect(filling, self.fill_colour, (0, 0, width, height), border_radius=radius)
            self.surface.blit(filling, self.gaps)  # In between surface to cut off end of rounded rect

            # Border
            if self.border_colour is not None:
                pygame.draw.rect(
                    self.surface, self.border_colour, rect, width=int(self.border_thickness), border_radius=radius
                )

        # Update text
        super().update()


class StackedProgressBar(_ProgressBarABC):
    @property
    def value(self) -> float:
        return self.values[self.show_layer]

    @property
    def show_layer(self) -> int:
        return self._show_layer

    @show_layer.setter
    def show_layer(self, value: int) -> None:
        self._show_layer = value
        if self.progress_value:
            self.text.text_str = f"{int(self.value)}/{int(self.max)}"

    @property
    def values(self) -> list[float]:
        return self._values

    @values.setter
    def values(self, value: list[float]) -> None:
        if self._values == value:
            return

        self._values = value
        if self.progress_value:
            self.text.text_str = f"{int(self.value)}/{int(self.max)}"
        self.dirty = True

    @property
    def fill_colours(self) -> list[Colour]:
        return self._fill_colours

    @fill_colours.setter
    def fill_colours(self, value: list[Colour]) -> None:
        if self._fill_colours == value:
            return

        self._fill_colours = value
        self.dirty = True

    def __init__(
        self,
        relative_pos: Vec2,
        size: Size,
        maximum: float,
        fill_colours: list[Colour],
        layers: int,
        show_layer: int = 0,
        progress_value: bool = False,  # Text showing progress value
        font: pygame.Font = None,
        background_colour: Colour = None,
        text_colour: Colour = (255, 255, 255),
        border_colour: Colour = None,
        border_thickness: int = 1,
        border_radius: int = 0,
        gaps: Vec2 = (0, 0),
        values: list[float] = None,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self._show_layer: int = show_layer
        self._values: list[float] = values or [0] * layers
        self._fill_colours: list[Colour] = fill_colours

        super().__init__(
            relative_pos,
            size,
            maximum,
            progress_value=progress_value,
            font=font,
            background_colour=background_colour,
            text_colour=text_colour,
            border_colour=border_colour,
            border_thickness=border_thickness,
            border_radius=border_radius,
            gaps=gaps,
            container=container,
            anchors=anchors,
        )

    def update(self) -> None:
        if self.dirty:
            self.surface = pygame.Surface(self.size, pygame.SRCALPHA).convert_alpha()
            rect = 0, 0, *self.size

            # Background
            radius = int(self.border_radius)
            if self.background_colour is not None:
                pygame.draw.rect(self.surface, self.background_colour, rect, border_radius=radius)

            # Filling
            prev_value = 0
            for i, value in enumerate(self.values):
                width = self.width - self.gaps[0] * 2
                height = self.height - self.gaps[1] * 2
                # In between surface to cut off end of rounded rect
                filling = pygame.Surface((width * (value / self.max), height), pygame.SRCALPHA)
                offset = width * (prev_value / self.max)
                pygame.draw.rect(filling, self.fill_colours[i], (-offset, 0, width, height), border_radius=radius)
                self.surface.blit(filling, (offset + self.gaps[0], self.gaps[1]))
                prev_value += value

            # Border
            if self.border_colour is not None:
                pygame.draw.rect(
                    self.surface, self.border_colour, rect, width=int(self.border_thickness), border_radius=radius
                )

        # Update text
        super().update()

    def set_value(self, value: float, layer: int) -> None:
        self.values[layer] = max(0, value)
        if self.progress_value and layer == self.show_layer:  # Update text
            self.text.text_str = f"{int(self.value)}/{int(self.max)}"
        self.dirty = True


class EventProgressBar(ProgressBar):
    def __init__(
        self,
        relative_pos: Vec2,
        size: Size,
        maximum: float,
        fill_colour: Colour,
        value_event: int,
        get_value: Callable[[pygame.Event], float],
        max_event: int | None = None,
        get_max: Callable[[pygame.Event], float] | None = None,
        progress_value: bool = False,  # Text showing progress value
        font: pygame.Font = None,
        background_colour: Colour = None,
        text_colour: Colour = (255, 255, 255),
        border_colour: Colour = None,
        border_thickness: int = 1,
        border_radius: int = 0,
        gaps: Vec2 = (0, 0),
        value: float = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.value_event: int = value_event
        self.event_get_value: Callable[[pygame.Event], float] = get_value
        self.max_event: int | None = max_event
        self.event_get_max: Callable[[pygame.Event], float] | None = get_max

        super().__init__(
            relative_pos,
            size,
            maximum,
            fill_colour,
            progress_value=progress_value,
            font=font,
            background_colour=background_colour,
            text_colour=text_colour,
            border_colour=border_colour,
            border_thickness=border_thickness,
            border_radius=border_radius,
            gaps=gaps,
            value=value,
            container=container,
            anchors=anchors,
        )

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == self.value_event:
            self.value = self.event_get_value(event)
        if event.type == self.max_event:
            self.max = self.event_get_max(event)


class EventStackedProgressBar(StackedProgressBar):
    def __init__(
        self,
        relative_pos: Vec2,
        size: Size,
        maximum: float,
        fill_colours: list[Colour],
        layers: int,
        value_event: int | list[int],
        get_value: Callable[[pygame.Event], float] | list[Callable[[pygame.Event], float]],
        max_event: int | None = None,
        get_max: Callable[[pygame.Event], float] | None = None,
        show_layer: int = 0,
        progress_value: bool = False,  # Text showing progress value
        font: pygame.Font = None,
        background_colour: Colour = None,
        text_colour: Colour = (255, 255, 255),
        border_colour: Colour = None,
        border_thickness: int = 1,
        border_radius: int = 0,
        gaps: Vec2 = (0, 0),
        values: list[float] = None,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        if isinstance(value_event, int):
            value_event = [value_event] * layers
        if callable(get_value):
            get_value = [get_value] * layers

        self.value_events: list[int] = value_event
        self.events_get_value: list[Callable[[pygame.Event], float]] = get_value
        self.max_event: int | None = max_event
        self.event_get_max: Callable[[pygame.Event], float] | None = get_max

        super().__init__(
            relative_pos,
            size,
            maximum,
            fill_colours,
            layers,
            show_layer=show_layer,
            progress_value=progress_value,
            font=font,
            background_colour=background_colour,
            text_colour=text_colour,
            border_colour=border_colour,
            border_thickness=border_thickness,
            border_radius=border_radius,
            gaps=gaps,
            values=values,
            container=container,
            anchors=anchors,
        )

    def handle_event(self, event: pygame.Event) -> None:
        # Layer values
        matches = [i for i, ev in enumerate(self.value_events) if event.type == ev]
        for match in matches:
            self.set_value(self.events_get_value[match](event), match)

        # Max
        if event.type == self.max_event:
            self.max = self.event_get_max(event)
