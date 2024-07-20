from abc import ABC, abstractmethod

import pygame
from util.func import normalise_for_drawing
from util.type import Colour, Drawable


class BoxABC(ABC):
    @property
    @abstractmethod
    def x() -> float:
        pass

    @property
    @abstractmethod
    def y() -> float:
        pass

    @property
    @abstractmethod
    def left() -> float:
        pass

    @property
    @abstractmethod
    def top() -> float:
        pass

    @property
    @abstractmethod
    def right() -> float:
        pass

    @property
    @abstractmethod
    def bottom() -> float:
        pass

    @property
    @abstractmethod
    def width() -> int:
        pass

    @property
    @abstractmethod
    def height() -> int:
        pass


class Box(BoxABC, Drawable):
    @property
    def x(self) -> float:
        """Alias for :obj:`left`."""
        return self.left

    @x.setter
    def x(self, value: float) -> None:
        self.left = value

    @property
    def y(self) -> float:
        """Alias for :obj:`top`."""
        return self.top

    @y.setter
    def y(self, value: float) -> None:
        self.top = value

    @property
    def left(self) -> float:
        """The left-most coordinate of this Box."""
        return self._left

    @left.setter
    def left(self, value: float) -> None:
        self._left = value

    @property
    def top(self) -> float:
        """The top-most coordinate of this Box."""
        return self._top

    @top.setter
    def top(self, value: float) -> None:
        self._top = value

    @property
    def right(self) -> float:
        """The right-most coordinate of this Box."""
        return self.left + self.width

    @right.setter
    def right(self, value: float) -> None:
        self.left = value - self.width

    @property
    def bottom(self) -> float:
        """The bottom-most coordinate of this Box."""
        return self.top + self.height

    @bottom.setter
    def bottom(self, value: float) -> None:
        self.top = value - self.height

    @property
    def width(self) -> int:
        """The width of this box."""
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        if value < 0:
            self.x -= value
        self._width = abs(value)

    @property
    def height(self) -> int:
        """The height of this box."""
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        if value < 0:
            self.y -= value
        self._height = abs(value)

    @property
    def center_x(self) -> float:
        """The x coordinate of the center of this Box."""
        return self.x + self.width / 2

    @center_x.setter
    def center_x(self, value) -> None:
        self.x = value - self.width / 2

    @property
    def center_y(self) -> float:
        """The y coordinate of the center of this Box."""
        return self.y + self.height / 2

    @center_y.setter
    def center_y(self, value) -> None:
        self.y = value - self.height / 2

    def __init__(self, x: float, y: float, width: int, height: int, **kwargs):
        self.left: float = x
        self.top: float = y
        self.width: int = width
        self.height: int = height
        super().__init__(**kwargs)

    def draw(
        self,
        surface: pygame.Surface,
        colour: Colour = (0, 0, 255),
        x_off: float = 0,
        y_off: float = 0,
        scale: float = 1,
    ) -> None:
        """Draws this box to the given surface.

        Parameters
        ----------
        surface : pygame.Surface
            The surface to draw to.
        colour : Colour, default = (0, 0, 255)
            The colour to draw this box as.
        x_off : float, default = 0
            The offset in the x direction to draw this box.
        y_off : float, default = 0
            The offset in the y direction to draw this box.
        scale : float, default = 1
            The scale to draw this box.
        """

        x, y, width, height = normalise_for_drawing(*self, x_off, y_off, scale)
        if width > 0 and height > 0:
            surface.fill(colour, (x, y, width, height))

    def to_json(self) -> dict[str, float | int]:
        """Converts this box to JSON format.

        Returns
        -------
        dict with str keys and float or int values
            The JSON representation of this box.
        """
        return {"x": self.x, "y": self.y, "w": self.width, "h": self.height}

    def __iter__(self):
        return iter((self.x, self.y, self.width, self.height))

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {{{self.left=}, {self.top=}, {self.right=}, {self.bottom=}}}"
