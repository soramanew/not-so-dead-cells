import pygame
from util.event import UI_BUTTON_PRESSED
from util.type import Colour, Side, Vec2

from .base import Panel, UIElement
from .text import ShadowText


class ShadowTextButton(ShadowText):
    @property
    def clicked(self) -> bool:
        return self._clicked

    @clicked.setter
    def clicked(self, value: bool) -> None:
        if self._clicked == value:
            return

        self._clicked = value

        click_diff = (self._shadow_off - self.shadow_off_clicked) * (1 if value else -1)
        self.relative_pos[0] += click_diff
        self.relative_pos[1] += click_diff

        self.dirty = True

    @property
    def hovered(self) -> bool:
        return self._hovered

    @hovered.setter
    def hovered(self, value: bool) -> None:
        if self._hovered == value:
            return

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if value else pygame.SYSTEM_CURSOR_ARROW)

        self._hovered = value
        self.dirty = True

    @property
    def colour(self) -> Colour:
        return self.hover_colour if self.hovered else self._colour

    @colour.setter
    def colour(self, value: Colour) -> None:
        if self._colour == value:
            return

        ShadowText.colour.fset(self, value)
        self.hover_colour = value[0] * 0.9, value[1] * 0.9, value[2] * 0.9

    @property
    def shadow_off(self) -> float:
        return self.shadow_off_clicked if self.clicked else self._shadow_off

    @shadow_off.setter
    def shadow_off(self, value: float) -> None:
        self._shadow_off = value
        self.shadow_off_clicked = self._shadow_off * self.clicked_depth

    def __init__(
        self,
        relative_pos: Vec2,
        font: pygame.Font,
        text: str,
        colour: Colour,
        depth: float = 1 / 15,
        clicked_depth: float = 0.7,
        wrap_length: int = 0,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self.clicked_depth: float = clicked_depth

        self._clicked: bool = False
        self._hovered: bool = False
        self.mouse_down: bool = False

        super().__init__(
            relative_pos, font, text, colour, depth=depth, wrap_length=wrap_length, container=container, anchors=anchors
        )

        self.hover_colour: Colour = colour[0] * 0.9, colour[1] * 0.9, colour[2] * 0.9

    def handle_event(self, event: pygame.Event) -> None:
        super().handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and self.collidepoint(*pygame.mouse.get_pos()):
            self.mouse_down = True
            self.clicked = True
        elif self.mouse_down and event.type == pygame.MOUSEBUTTONUP:
            self.mouse_down = False
            self.clicked = False
            if self.collidepoint(*pygame.mouse.get_pos()):
                pygame.event.post(pygame.Event(UI_BUTTON_PRESSED, element=self))
        elif event.type == pygame.MOUSEMOTION:
            if self.collidepoint(*pygame.mouse.get_pos()):
                self.hovered = True
                if self.mouse_down:
                    self.clicked = True
            else:
                self.hovered = False
                self.clicked = False


class Checkbox(ShadowTextButton):
    SPACING: float = 0.4
    THICKNESS: float = 0.2
    INNER_SPACING: float = 0.14

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        if self._checked == value:
            return

        self._checked = value
        self.dirty = True

    @property
    def text(self) -> pygame.Surface:
        return self._text

    @text.setter
    def text(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._text = pygame.Surface(
            (rect.width + rect.height * (1 + Checkbox.SPACING), rect.height), pygame.SRCALPHA
        ).convert_alpha()
        self._text.blit(value, (0, 0), rect)
        colour = self.hover_colour if self.hovered else self.colour
        thickness = int(rect.height * Checkbox.THICKNESS)
        inner_gap = thickness + int(rect.height * Checkbox.INNER_SPACING)
        x = rect.width + int(rect.height * Checkbox.SPACING)
        pygame.draw.rect(self._text, colour, (x, 0, rect.height, rect.height), width=thickness)
        if self.checked:
            pygame.draw.rect(
                self._text,
                colour,
                (x + inner_gap, inner_gap, rect.height - inner_gap * 2, rect.height - inner_gap * 2),
            )
        self.size = self._text.size

    @property
    def shadow(self) -> pygame.Surface:
        return self._shadow

    @shadow.setter
    def shadow(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._shadow = pygame.Surface(
            (rect.width + rect.height * (1 + Checkbox.SPACING), rect.height), pygame.SRCALPHA
        ).convert_alpha()
        self._shadow.blit(value, (0, 0), rect)
        thickness = int(rect.height * Checkbox.THICKNESS)
        inner_gap = thickness + int(rect.height * Checkbox.INNER_SPACING)
        x = rect.width + int(rect.height * Checkbox.SPACING)
        pygame.draw.rect(self._shadow, self.shadow_colour, (x, 0, rect.height, rect.height), width=thickness)
        if self.checked:
            pygame.draw.rect(
                self._shadow,
                self.shadow_colour,
                (x + inner_gap, inner_gap, rect.height - inner_gap * 2, rect.height - inner_gap * 2),
            )

    def __init__(
        self,
        relative_pos: Vec2,
        font: pygame.Font,
        text: str,
        colour: Colour,
        depth: float = 1 / 15,
        clicked_depth: float = 0.7,
        wrap_length: int = 0,
        checked: bool = False,
        side: Side = Side.RIGHT,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        self._checked: bool = checked
        self.side: Side = side
        super().__init__(
            relative_pos,
            font,
            text,
            colour,
            depth=depth,
            clicked_depth=clicked_depth,
            wrap_length=wrap_length,
            container=container,
            anchors=anchors,
        )

    def handle_event(self, event: pygame.Event) -> None:
        if self.mouse_down and event.type == pygame.MOUSEBUTTONUP:
            if self.collidepoint(*pygame.mouse.get_pos()):
                self.checked = not self.checked

        super().handle_event(event)
