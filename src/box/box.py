import pygame
from util.func import comp_as_int, strict_eq


class Box:
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
        """float : The left-most coordinate of this Box.

        Links to :obj:`_rect`.
        """
        return self._left

    @left.setter
    def left(self, value: float):
        self._left = value

    @property
    def top(self):
        """float : The top-most coordinate of this Box.

        Links to :obj:`_rect`.
        """
        return self._top

    @top.setter
    def top(self, value: float):
        self._top = value

    @property
    def right(self):
        """float : The right-most coordinate of this Box.

        Links to :obj:`left` and :obj:`_rect`.
        """
        return self.left + self.width

    @right.setter
    def right(self, value: float):
        self.left = value - self.width

    @property
    def bottom(self):
        """float : The bottom-most coordinate of this Box.

        Links to :obj:`top` and :obj:`_rect`.
        """
        return self.top + self.height

    @bottom.setter
    def bottom(self, value: float):
        self.top = value - self.height

    @property
    def width(self):
        """The width of this box."""
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        """The height of this box."""
        return self._height

    @height.setter
    def height(self, value):
        self._height = value

    @property
    def center_x(self):
        return self.x + self.width / 2

    @center_x.setter
    def center_x(self, value):
        self.x = value - self.width / 2

    @property
    def center_y(self):
        return self.y + self.height / 2

    @center_y.setter
    def center_y(self, value):
        self.y = value - self.height / 2

    def __init__(self, x: float, y: float, width: int, height: int):
        self.left = x
        self.top = y
        self.width = width
        self.height = height

    def draw(
        self,
        window: pygame.Surface,
        colour: tuple[int, int, int] = (0, 0, 255),
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        """Draws this box to the given surface.

        Parameters
        ----------
        window : pygame.Surface
            The surface to draw to.
        colour : tuple[int, int, int], default = (0, 0, 255)
            The colour to draw this box as.
        x_off : float, default = 0
            The offset in the x direction to draw this box.
        y_off : float, default = 0
            The offset in the y direction to draw this box.
        scale : float, default = 1
            The scale to draw this box.
        """

        x = (self.x + x_off) * scale
        y = (self.y + y_off) * scale
        width = self.width * scale
        height = self.height * scale
        if x < 0:
            width += x
            x = 0
        if y < 0:
            height += y
            y = 0
        window.fill(colour, (x, y, width, height))

    def to_json(self) -> dict[str, float | int]:
        """Converts this box to JSON format.

        Returns
        -------
        dict with str keys and float or int values
            The JSON representation of this box.
        """
        return {"x": self.x, "y": self.y, "w": self.width, "h": self.height}
        # return "{" + '"x":{x},"y":{y},"w":{w},"h":{h}'.format(x=self.x, y=self.y, w=self.width, h=self.height) + "}"

    def __hash__(self) -> int:
        return hash((int(self.x), int(self.y), self.width, self.height))

    def __eq__(self, other) -> bool:
        if strict_eq(self, other):
            return (
                comp_as_int(self.x, other.x)
                and comp_as_int(self.y, other.y)
                and self.width == other.width
                and self.height == other.height
            )
        else:
            return False