import pygame
import state
from box import Box
from enemy.enemy import Enemy
from map import DamageNumber
from util.type import Drawable, Interactable, Rect, Vec2


class Camera(Box):
    # The length of the animation of the camera moving to center on the target
    TARGET_MOVE_ANIM_LENGTH: float = 0.5
    # The amount outside the screen in which to tick entities
    ACTIVE_AREA: int = 500

    @property
    def active_bounds(self) -> Rect:
        return (
            max(0, self.x - Camera.ACTIVE_AREA),
            max(0, self.y - Camera.ACTIVE_AREA),
            min(state.current_map.width, self.width + Camera.ACTIVE_AREA * 2),
            min(state.current_map.height, self.height + Camera.ACTIVE_AREA * 2),
        )

    def __init__(self):
        super().__init__(0, 0, *pygame.display.get_window_size())

    def instant_center(self) -> None:
        self.move(state.player.center_x - self.center_x, state.player.center_y - self.center_y)

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

    def tick_move(self, dt: float) -> Vec2:
        """Moves this camera's viewport to center on the target.

        This is a tick method and thus should be called once per tick.

        Parameters
        ----------
        dt : float
            The time between this tick and the last.

        Returns
        -------
        Vec2
            The amount the viewport moved by.
        """

        dx = (state.player.center_x - self.center_x) / Camera.TARGET_MOVE_ANIM_LENGTH * dt
        dy = (state.player.center_y - self.center_y) / Camera.TARGET_MOVE_ANIM_LENGTH * dt
        self.move(dx, dy)
        return dx, dy

    def _render_w_off(self, target: Drawable, window: pygame.Surface, **kwargs) -> None:
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

    def render(self, window: pygame.Surface) -> None:
        """Renders the given map to the given surface through this camera's viewport.

        See Also
        --------
        _render_w_off()
        render_debug()

        Parameters
        ----------
        window : pygame.Surface
            The surface to render to.
        """

        # Background
        if state.current_map.static_bg:
            window.fill(state.current_map.background)
        else:
            state.current_map.background.draw(window)

        # Map texture
        window.blit(state.current_map.texture, (0, 0), (self.x, self.y, self.width, self.height))

        # Entities (enemies, etc)
        for drawable in state.current_map.get_rect(*self, lambda client: isinstance(client, Drawable)):
            self._render_w_off(drawable, window)

        # Player
        self._render_w_off(state.player, window)

        # Enemy health bars
        for enemy in state.current_map.get_rect(*self, lambda client: isinstance(client, Enemy)):
            enemy.draw_health_bar(window, x_off=-self.x, y_off=-self.y)

        # Damage numbers
        for dm in state.current_map.get_rect(*self, lambda e: isinstance(e, DamageNumber)):
            self._render_w_off(dm, window)

        # Interactable popups
        for i in state.current_map.get_rect(*state.player.interact_range, lambda e: isinstance(e, Interactable)):
            i.draw_popup(window, x_off=-self.x, y_off=-self.y)
