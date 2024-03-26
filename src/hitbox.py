from __future__ import annotations

from box import Box
from util_types import Direction, Collision


class Hitbox(Box):
    def __init__(self, x: float, y: float, width: int, height: int):
        super().__init__(x, y, width, height)

    def __str__(self) -> str:
        return f"Hitbox [ {self.left=}, {self.top=}, {self.right=}, {self.bottom=} ]"

    def move(self, dx: float, dy: float, boxes: set[Hitbox]) -> list[Collision]:
        """Moves this Hitbox by a given amount while checking for collisions.

        This method calls move_axis for each axis.

        See Also
        --------
        move_axis()

        Parameters
        ----------
        dx : float
            The number of pixels to move in the x-axis.
        dy : float
            The number of pixels to move in the y-axis.
        boxes : set of Hitbox
            A set of other Hitboxes to check for collisions with.

        Returns
        -------
        list of Collision
            The list of collisions.
        """

        collisions = []

        if dx != 0:
            collisions += self.move_axis(dx, 0, boxes)
        if dy != 0:
            collisions += self.move_axis(0, dy, boxes)

        return collisions

    def move_axis(self, dx: float, dy: float, boxes: set[Hitbox]) -> list[Collision]:
        """Moves this Hitbox by a given amount while checking for collisions with other Hitboxes.

        Only use this method for single axis movement; Use move() for movement.

        See Also
        --------
        move()

        Parameters
        ----------
        dx : float
            The number of pixels to move in the x-axis.
        dy : float
            The number of pixels to move in the y-axis.
        boxes : set of Hitbox
            A set of other Hitboxes to check for collisions with.

        Returns
        -------
        list of Direction
            A list of directions which collisions happened in.
        """

        self.x += dx
        self.y += dy

        collisions = []

        for box in boxes:
            if self._rect.colliderect(box._rect):
                if dx > 0:
                    collisions.append(Collision(Direction.RIGHT, box))
                    self.right = box.left
                elif dx < 0:
                    collisions.append(Collision(Direction.LEFT, box))
                    self.left = box.right
                if dy > 0:
                    collisions.append(Collision(Direction.DOWN, box))
                    self.bottom = box.top
                elif dy < 0:
                    collisions.append(Collision(Direction.UP, box))
                    self.top = box.bottom

        return collisions
