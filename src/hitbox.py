from __future__ import annotations

import pygame


class Hitbox:
    def __init__(self, x: float, y: float, width: int, height: int):
        self._rect = pygame.Rect(x, y, width, height)
        self.left = x
        self.top = y

    def __str__(self):
        return f"Hitbox [ {self.left=}, {self.top=}, {self.right=}, {self.bottom=} ]"

    @property
    def x(self):
        """Alias for :obj:`left`."""
        return self.left

    @x.setter
    def x(self, value: float):
        self.left = value

    @property
    def y(self):
        """Alias for :obj:`top`."""
        return self.top

    @y.setter
    def y(self, value: float):
        self.top = value

    @property
    def left(self):
        """float : The left-most coordinate of this Hitbox.

        Links to :obj:`_rect`.
        """
        return self._left

    @left.setter
    def left(self, value: float):
        self._left = value
        self._rect.left = self.left

    @property
    def top(self):
        """float : The top-most coordinate of this Hitbox.

        Links to :obj:`_rect`.
        """
        return self._top

    @top.setter
    def top(self, value: float):
        self._top = value
        self._rect.top = self.top

    @property
    def right(self):
        """float : The right-most coordinate of this Hitbox.

        Links to :obj:`left` and :obj:`_rect`.
        """
        return self.left + self._rect.width

    @right.setter
    def right(self, value: float):
        self.left = value - self._rect.width
        self._rect.right = self.right

    @property
    def bottom(self):
        """float : The bottom-most coordinate of this Hitbox.

        Links to :obj:`top` and :obj:`_rect`.
        """
        return self.top + self._rect.height

    @bottom.setter
    def bottom(self, value: float):
        self.top = value - self._rect.height
        self._rect.bottom = self.bottom

    @property
    def width(self):
        """The width of this Hitbox."""
        return self._rect.width

    @width.setter
    def width(self, value):
        self._rect.width = value

    @property
    def height(self):
        """The height of this Hitbox."""
        return self._rect.height

    @height.setter
    def height(self, value):
        self._rect.height = value

    def move(self, dx, dy, boxes):
        """Moves this hitbox by a given amount while checking for collisions.

        This method calls :func:`move_axis<Hitbox.move_axis>` for each axis.

        Parameters
        ----------
        dx : float
            The number of pixels to move in the x-axis.
        dy : float
            The number of pixels to move in the y-axis.
        boxes : list of Hitbox
            A list of other Hitboxes to check for collisions with.

        Returns
        -------
        list of str
            A list of directions which collisions happened in. Can be left, right, top or bottom.
        """

        collisions = []

        if dx != 0:
            collisions += self.move_axis(dx, 0, boxes)
        if dy != 0:
            collisions += self.move_axis(0, dy, boxes)

        return collisions

    def move_axis(self, dx, dy, boxes):
        """Moves this Hitbox by a given amount while checking for collisions with other Hitboxes.

        Only use this method for single axis movement; Use :func:`move<Hitbox.move>` for movement.

        Parameters
        ----------
        dx : float
            The number of pixels to move in the x-axis.
        dy : float
            The number of pixels to move in the y-axis.
        boxes : list of Hitbox
            A list of other Hitboxes to check for collisions with.

        Returns
        -------
        list of str
            A list of directions which collisions happened in. Can be 'left', 'right', 'top' or 'bottom'.
        """

        self.x += dx
        self.y += dy

        collisions = []

        for box in boxes:
            if self._rect.colliderect(box._rect):
                if dx > 0:
                    collisions.append("right")
                    self.right = box.left
                elif dx < 0:
                    collisions.append("left")
                    self.left = box.right
                if dy > 0:
                    collisions.append("bottom")
                    self.bottom = box.top
                elif dy < 0:
                    collisions.append("top")
                    self.top = box.bottom

        return collisions

    def draw(self, window: pygame.Surface, colour=(0, 0, 255)):
        window.fill(colour, self._rect)
