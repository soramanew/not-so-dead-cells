from __future__ import annotations

import pygame
from util.type import Size, Vec2


class UIElement(pygame.FRect):
    def __init__(
        self, relative_pos: Vec2, size: Size, container: Panel = None, anchors: dict[str, str | UIElement] = None
    ):
        super().__init__(0, 0, *size)

        # Position relative to anchors
        self.relative_pos: Vec2 = list(relative_pos)

        # Parent container or window if none
        self.container: Panel | pygame.Surface = pygame.display.get_surface() if container is None else container
        if container is not None:  # FRect with 0 size is falsy
            container.add_child(self)

        # Default anchor top left
        self.anchors: dict[str, str | UIElement] = anchors or {"left": "left", "top": "top"}
        # Only center is valid when less than 2 keys (targets don't count)
        # Since measuring by num keys, technically you could have all anchors on the same axis, which is not supposed to happen (you need at least 1 anchor for each axis)
        if anchors and len([a for a in anchors if not a.endswith("_target")]) < 2 and "center" not in anchors:
            # Insert default anchor for other axis if only one axis' anchor is given
            if "left" in anchors or "right" in anchors or "centerx" in anchors:
                self.anchors.update({"top": "top"})
            else:
                self.anchors.update({"left": "left"})

        # If this ui element needs to be updated, true on init cause needs to be updated
        self.dirty: bool = True

        # Init update position and anything else
        self.update()

    def set_container(self, container: Panel) -> None:
        if isinstance(self.container, Panel):
            self.container.remove_child(self)
        self.container = container
        container.add_child(self)

    def update_position(self) -> None:
        """Updates the position of this ui element based on the size and position of it's container."""

        width, height = self.container.size

        # Center is special, it centers both axes
        if "center" in self.anchors:
            self.center = width / 2, height / 2

        # For each side + center axes
        for side in "left", "top", "right", "bottom", "centerx", "centery":
            if side in self.anchors:
                side_anchor = self.anchors[side]
                if f"{side}_target" in self.anchors:
                    # Set self.side to the anchor target's side which self is anchored to
                    setattr(self, side, getattr(self.anchors[f"{side}_target"], side_anchor))
                elif side_anchor == "left" or side_anchor == "top":
                    setattr(self, side, 0)
                elif side_anchor == "right":
                    setattr(self, side, width)
                elif side_anchor == "bottom":
                    setattr(self, side, height)
                elif side_anchor == "centerx":
                    setattr(self, side, width / 2)
                elif side_anchor == "centery":
                    setattr(self, side, height / 2)

        # Add relative position
        self.move_ip(self.relative_pos)

        # Move to container position (window is (0, 0) and doesn't have topleft attribute)
        if hasattr(self.container, "topleft"):
            # Don't move target anchor axis
            move_x = True
            move_y = True
            for side in "left", "top", "right", "bottom", "centerx", "centery":
                if f"{side}_target" in self.anchors:
                    if side == "left" or side == "right" or side == "centerx":
                        move_x = False
                    else:
                        move_y = False
                # Early break cause no need for further checking
                if not (move_x or move_y):
                    break
            # Move
            if move_x:
                self.x += self.container.left
            if move_y:
                self.y += self.container.top

    def scale_by_ip(self, x: float, y: float = None) -> None:
        if y is None:
            y = x

        super().scale_by_ip(x, y)

        self.relative_pos[0] *= x
        self.relative_pos[1] *= y

        self.dirty = True

    def update(self) -> None:
        """Updates this ui element if it is dirty. This should be called once per frame."""

        if self.dirty:
            self.update_position()
            self.dirty = False

    def handle_event(self, event: pygame.Event) -> None:
        """Handles the given event. This should be called per event.

        Parameters
        ----------
        event : pygame.Event
            The event to handle.
        """

    def draw(self, surface: pygame.Surface) -> None:
        """Draws this ui element and its children to the given surface.

        Parameters
        ----------
        surface : pygame.Surface
            The surface to draw to.
        """


class Panel(UIElement):
    def __init__(
        self,
        relative_pos: Vec2,
        size: Size = None,
        container: Panel = None,
        anchors: dict[str, str | UIElement] = None,
    ):
        # Don't reset children if already has (created in subclasses)
        if not hasattr(self, "children"):
            self.children: list[UIElement] = []

        self.dynamic_size: bool = size is None

        super().__init__(relative_pos, (0, 0) if size is None else size, container=container, anchors=anchors)

    def add_child(self, child: UIElement) -> None:
        self.children.append(child)

    def remove_child(self, child: UIElement) -> None:
        self.children.remove(child)

    def pack(self, recursion_depth: int = 0) -> None:
        if self.children:
            if recursion_depth != 0:  # Negative means infinite recursion
                for child in self.children:
                    if isinstance(child, Panel):
                        child.pack(recursion_depth - 1)

            left_top = [min(getattr(child, side) for child in self.children) for side in ("left", "top")]  # Min
            right_bottom = [max(getattr(child, side) for child in self.children) for side in ("right", "bottom")]  # Max
            self.x, self.y = left_top
            self.width = right_bottom[0] - left_top[0]
            self.height = right_bottom[1] - left_top[1]
        else:
            # No children so no size
            self.size = 0, 0

    def update_position(self) -> None:
        if self.dynamic_size:
            self.pack()

        super().update_position()

        for child in self.children:
            child.update_position()

    def scale_by_ip(self, x: float, y: float = None) -> None:
        if y is None:
            y = x

        super().scale_by_ip(x, y)

        for child in self.children:
            child.scale_by_ip(x, y)

    def handle_event(self, event: pygame.Event) -> None:
        for child in self.children:
            child.handle_event(event)

    def update(self) -> None:
        super().update()

        for child in self.children:
            child.update()

    def draw(self, surface: pygame.Surface) -> None:
        for child in self.children:
            child.draw(surface)
