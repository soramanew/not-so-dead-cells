import pygame
from box import Box, Hitbox
from map import Map


class Camera(Box):
    # The length of the animation of the camera moving to center on the target
    TARGET_MOVE_ANIM_LENGTH = 0.5

    def __init__(self, target: Box, width: int, height: int, x: float = 0, y: float = 0) -> None:
        super().__init__(x, y, width, height)
        self.target = target

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

    def tick_move(self, dt: float) -> None:
        """Moves this camera's viewport to center on the target.

        This is a tick method and thus should be called once per tick.

        Parameters
        ----------
        dt : float
            The time between this tick and the last.
        """

        dx = (self.target.center_x - self.center_x) / Camera.TARGET_MOVE_ANIM_LENGTH * dt
        dy = (self.target.center_y - self.center_y) / Camera.TARGET_MOVE_ANIM_LENGTH * dt
        self.move(dx, dy)

    def _render_w_off(self, target: Box, window: pygame.Surface, **kwargs) -> None:
        """Renders the given target to the given surface through this camera's viewport.

        This method draws the target to the surface with an offset of the negative of this camera's position.

        Parameters
        ----------
        target : Box
            The target to render.
        window : pygame.Surface
            The surface to render to.
        kwargs
            Additional arguments to pass to the target's draw method.
        """

        target.draw(window, x_off=-self.x, y_off=-self.y, **kwargs)

    def render_debug(self, window: pygame.Surface, current_map: Map) -> None:
        """Renders the given map in debug mode to the given surface through this camera's viewport.

        This method renders the map's Hitboxes.

        See Also
        --------
        _render_w_off()

        Parameters
        ----------
        window : pygame.Surface
            The surface to render to.
        current_map : Map
            The map to render in debug mode.
        """

        hitboxes = current_map.get_rect(
            self.x,
            self.y,
            self.width,
            self.height,
            lambda client: isinstance(client, Hitbox),
        )
        for hitbox in hitboxes:
            self._render_w_off(hitbox, window)

    def render(self, window: pygame.Surface, current_map: Map, debug: bool = False) -> None:
        """Renders the given map to the given surface through this camera's viewport.

        See Also
        --------
        _render_w_off()
        render_debug()

        Parameters
        ----------
        window : pygame.Surface
            The surface to render to.
        current_map : Map
            The map to render.
        debug : bool, default = False
            Whether to render the map in debug mode or not.
        """

        # TODO: render map texture
        if debug:
            self.render_debug(window, current_map)
        self._render_w_off(self.target, window, colour=(0, 255, 0))
