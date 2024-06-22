from __future__ import annotations

from util.type import Collision, Direction

from .box import Box


class Hitbox(Box):
    def move(self, dx: float, dy: float, boxes: set[Hitbox] | None = None) -> list[Collision]:
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

    def move_axis(self, dx: float, dy: float, boxes: set[Hitbox] | None = None) -> list[Collision]:
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

        if boxes is not None:
            for box in boxes:
                if self.detect_collision_box(box):
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

    def detect_collision(self, left: float, top: float, right: float, bottom: float) -> bool:
        return self.left < right and self.right > left and self.top < bottom and self.bottom > top

    def detect_collision_box(self, box: Box) -> bool:
        return self.detect_collision(box.left, box.top, box.right, box.bottom)

    def detect_collision_rect(self, left: float, top: float, width: int, height: int) -> bool:
        return self.detect_collision(left, top, left + width, top + height)
