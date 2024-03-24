from __future__ import annotations

import pygame

from src.box import Box


class Hitbox(Box):
    def __init__(self, x: float, y: float, width: int, height: int):
        super().__init__(x, y, width, height)

    def __str__(self):
        return f"Hitbox [ {self.left=}, {self.top=}, {self.right=}, {self.bottom=} ]"

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
