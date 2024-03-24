import re
from collections.abc import Callable

from pygame import Surface

from src.box import Box
from src.hitbox import Hitbox
from src.map import Map


class Camera(Box):

    CROSSHAIR_COLOUR = 255, 255, 255
    CROSSHAIR_SIZE = 10
    CROSSHAIR_THICKNESS = 2

    SPEED = 100
    FAST_MULT = 3

    def __init__(self, width: int, height: int, x: float = 0, y: float = 0, initial_scale: float = 1):
        super().__init__(x, y, width, height)
        self.scale = initial_scale

    def move(self, x: float, y: float) -> None:
        """Moves this camera's viewport by the given amount.

        Parameters
        ----------
        x : float
            The number of pixels to move in the x direction.
        y : float
            The number of pixels to move in the y direction.
        """

        self.x += x
        self.y += y

    def resize(self, width: int, height: int) -> None:
        """Resizes this camera's viewport to the given size.

        Parameters
        ----------
        width : int
            The new width of the viewport.
        height : int
            The new height of the viewport.
        """

        self.width = width
        self.height = height

    def _render_individual(self, target: Box, window: Surface, **kwargs) -> None:
        """Renders the given target to the given surface through this camera's viewport.

        This method draws the target to the surface with an offset of the negative of this camera's position
        and with this camera's scale.

        Parameters
        ----------
        target : Box
            The target to render.
        window : Surface
            The surface to render to.
        kwargs
            Additional arguments to pass to the target's draw method.
        """

        target.draw(window, x_off=-self.x, y_off=-self.y, scale=self.scale, **kwargs)

    def render_debug(self, window: Surface, current_map: Map) -> None:
        """Renders the given map in debug mode to the given surface through this camera's viewport.

        This method renders the map's Hitboxes.

        See Also
        --------
        _render_individual()

        Parameters
        ----------
        window : Surface
            The surface to render to.
        current_map : Map
            The map to render in debug mode.
        """

        hitboxes = current_map.get_rect(self.x, self.y, self.width, self.height,
                                        lambda client: isinstance(client, Hitbox))
        for hitbox in hitboxes:
            self._render_individual(hitbox, window)

    def render(self, window: Surface, current_map: Map, debug: bool = True,
               render_fn: Callable[[Surface], None] = None) -> None:
        """Renders the given map to the given surface through this camera's viewport.

        See Also
        --------
        render_debug()
        _render_crosshair()

        Parameters
        ----------
        window : Surface
            The surface to render to.
        current_map : Map
            The map to render.
        debug : bool, default = True
            Whether to render the map in debug mode or not.
        render_fn : Callable with parameters [Surface] and return None, optional
            An optional extra function to call between rendering the map and crosshair.
        """

        # TODO: render map texture
        if debug:
            self.render_debug(window, current_map)
        if callable(render_fn):
            render_fn(window)
        self._render_crosshair(window)

    def _render_crosshair(self, window: Surface) -> None:
        """Renders a crosshair in the center of the window.

        Parameters
        ----------
        window : Surface
            The window to render to.
        """
        vertical_rect = ((self.width - Camera.CROSSHAIR_SIZE) / 2, (self.height - Camera.CROSSHAIR_THICKNESS) / 2,
                         Camera.CROSSHAIR_SIZE, Camera.CROSSHAIR_THICKNESS)
        horizontal_rect = ((self.width - Camera.CROSSHAIR_THICKNESS) / 2, (self.height - Camera.CROSSHAIR_SIZE) / 2,
                           Camera.CROSSHAIR_THICKNESS, Camera.CROSSHAIR_SIZE)
        window.fill(Camera.CROSSHAIR_COLOUR, vertical_rect)
        window.fill(Camera.CROSSHAIR_COLOUR, horizontal_rect)
