from typing import Any, Callable

import pygame
from util.type import Colour, Vec2

from .base import Panel, UIElement


class Text(UIElement):
    @property
    def font(self) -> pygame.Font:
        return self._font

    @font.setter
    def font(self, value: pygame.Font) -> None:
        self._font = value
        self.font_size = value.point_size  # Update font size
        self.dirty = True

    @property
    def text_str(self) -> str:
        return self._text_str

    @text_str.setter
    def text_str(self, value: str) -> None:
        if self._text_str == value:
            return

        self._text_str = value
        self.dirty = True

    @property
    def colour(self) -> Colour:
        return self._colour

    @colour.setter
    def colour(self, value: Colour) -> None:
        if self._colour == value:
            return

        self._colour = value
        self.dirty = True

    @property
    def wrap_length(self) -> float:
        return self._wrap_length

    @wrap_length.setter
    def wrap_length(self, value: float) -> None:
        if self._wrap_length == value:
            return

        self._wrap_length = value
        self.dirty = True

    @property
    def font_size(self) -> float:
        return self._font_size

    @font_size.setter
    def font_size(self, value: float) -> None:
        if self._font_size == value:
            return

        self._font_size = value
        self.font.point_size = int(value)
        self.dirty = True

    @property
    def text(self) -> pygame.Surface:
        return self._text

    @text.setter
    def text(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._text = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        self._text.blit(value, (0, 0), rect)
        self.size = self._text.size

    def __init__(
        self,
        relative_pos: Vec2,
        font: pygame.Font,
        text: str,
        colour: Colour = (255, 255, 255),
        wrap_length: float = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self._font: pygame.Font = font
        self._font_size: float = font.point_size
        self._text_str: str = text
        self._colour: Colour = colour
        self._wrap_length: float = wrap_length

        self._text: pygame.Surface = None

        # Size (0, 0) cause it will be updated when init update is called
        super().__init__(relative_pos, (0, 0), container=container, anchors=anchors)

    # Extra arg to match signature
    def scale_by_ip(self, scale_by: float, _=None) -> None:
        super().scale_by_ip(scale_by)

        self.font_size *= scale_by
        self.wrap_length *= scale_by

    def update(self) -> None:
        if not self.dirty:
            return

        self.text = self.font.render(self.text_str, True, self.colour, wraplength=int(self.wrap_length))

        super().update()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.text, self.topleft)


class ShadowText(Text):
    @Text.colour.setter
    def colour(self, value: Colour) -> None:
        if self._colour == value:
            return

        Text.colour.fset(self, value)
        self.shadow_colour = value[0] * 0.1, value[1] * 0.1, value[2] * 0.1

    @Text.font_size.setter
    def font_size(self, value: float) -> None:
        if self._font_size == value:
            return

        Text.font_size.fset(self, value)
        self.shadow_off = 1 + self.font.point_size * self.depth

    @property
    def shadow(self) -> pygame.Surface:
        return self._shadow

    @shadow.setter
    def shadow(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._shadow = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        self._shadow.blit(value, (0, 0), rect)

    def __init__(
        self,
        relative_pos: Vec2,
        font: pygame.Font,
        text: str,
        colour: Colour,
        wrap_length: float = 0,
        depth: float = 1 / 15,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.shadow_colour: Colour = colour[0] * 0.1, colour[1] * 0.1, colour[2] * 0.1
        self.shadow_off: float = 1 + font.point_size * depth
        self.depth: float = depth

        self._shadow: pygame.Surface = None

        super().__init__(
            relative_pos, font, text, colour, wrap_length=wrap_length, container=container, anchors=anchors
        )

    def update(self) -> None:
        if not self.dirty:
            return

        self.shadow = self.font.render(self.text_str, True, self.shadow_colour, wraplength=int(self.wrap_length))

        super().update()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.shadow, (self.x + self.shadow_off, self.y + self.shadow_off))
        super().draw(surface)


class TextGroup(Panel):
    def __init__(
        self,
        relative_pos: Vec2,
        font: pygame.Font | list[pygame.Font],
        texts: list[str],
        spacing: float = 0,
        h_align: str = "center",
        colour: Colour = (255, 255, 255),
        wrap_length: float = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.children: list[Text] = []

        if isinstance(font, pygame.Font):
            font = [font] * len(texts)

        if h_align == "center":
            h_align = {"centerx": "centerx"}
        elif h_align == "right":
            h_align = {"right": "right"}
        else:
            h_align = {"left": "left"}

        for i, text in enumerate(texts):
            Text(
                (0, spacing if i > 0 else 0),
                font[i],
                text,
                container=self,
                anchors={**h_align, "top": "bottom", "top_target": self.children[i - 1]} if i > 0 else h_align,
            )

        super().__init__(relative_pos, container=container, anchors=anchors)


class EventText(Text):
    def __init__(
        self,
        relative_pos: Vec2,
        font: pygame.Font,
        format_text: str,
        event: int,
        get_value: Callable[[pygame.Event], Any],
        defaults: Any,
        colour: Colour = (255, 255, 255),
        wrap_length: float = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.format_text: str = format_text
        self.event: int = event
        self.get_value: Callable[[pygame.Event], str] = get_value

        try:
            default_text = format_text.format(*defaults)
        except TypeError:
            default_text = format_text.format(defaults)

        super().__init__(
            relative_pos,
            font,
            default_text,
            colour=colour,
            wrap_length=wrap_length,
            container=container,
            anchors=anchors,
        )

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == self.event:
            try:  # If multiple args
                self.text_str = self.format_text.format(*self.get_value(event))
            except TypeError:
                self.text_str = self.format_text.format(self.get_value(event))

    def set_value(self, *values: Any) -> None:
        self.text_str = self.format_text.format(*values)
