import sys

import pygame
from box import Box
from map import Map, Wall
from util.func import normalise_rect
from util.type import Rect, Vec2

from .camera import Camera


class Builder:
    SELECTION_COLOUR = 255, 255, 255, 120

    def __init__(self, window: pygame.Surface, zone: str, width: int, height: int):
        self.window = window
        self.map = Map(zone, load=False, width=width, height=height)
        self.map_box = Box(0, 0, width, height)
        self.camera = Camera(width, height)
        self.selection_start: Vec2 | tuple = ()
        self.selection: Rect | tuple = ()
        self.has_selection = False

    def main_loop(self):
        clock = pygame.time.Clock()
        l_dragging = False
        r_dragging = False
        prev_mouse_pos = 0, 0
        while True:
            dt = clock.tick(60) / 1000  # To get in seconds

            selection_changed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.camera.resize(*event.dict["size"])
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.select()
                    elif event.key == pygame.K_RETURN:
                        if self.has_selection:
                            self.add_wall()
                    elif event.key == pygame.K_s and pygame.key.get_mods() & (pygame.KMOD_CTRL | pygame.KMOD_ALT):
                        self.map.save()
                    elif event.key == pygame.K_p:
                        self.set_player()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        l_dragging = True
                        self.selection_start = self.camera.get_absolute(*event.pos)
                    elif event.button == 2:
                        r_dragging = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        l_dragging = False
                        self.has_selection = True
                    elif event.button == 2:
                        r_dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    if l_dragging:
                        self.handle_l_drag(event.pos)
                        selection_changed = True
                    if r_dragging:
                        self.handle_r_drag(prev_mouse_pos, event.pos)
                    prev_mouse_pos = event.pos

            keys = pygame.key.get_pressed()
            speed_mod = Camera.FAST_MULT if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.camera.move(-Camera.SPEED * speed_mod * dt, 0)
                selection_changed = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.camera.move(Camera.SPEED * speed_mod * dt, 0)
                selection_changed = True
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.camera.move(0, -Camera.SPEED * speed_mod * dt)
                selection_changed = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.camera.move(0, Camera.SPEED * speed_mod * dt)
                selection_changed = True

            if selection_changed and not self.has_selection and len(self.selection_start) == 2:
                self.selection = normalise_rect(
                    *self.selection_start,
                    int(self.camera.center_x - self.selection_start[0]),
                    int(self.camera.center_y - self.selection_start[1]),
                )

            self.window.fill((50, 50, 50))
            self.map_box.draw(self.window, (0, 0, 0), x_off=-self.camera.x, y_off=-self.camera.y)
            self.camera.render(self.window, self.map, render_fn=self._render_selection)
            pygame.display.update()

    def select(self) -> None:
        """Handles the select action by setting the start of the selection and toggling has_selection.

        This method is for selecting with the keyboard *not* the mouse.
        """

        if len(self.selection_start) == 0 or self.has_selection:
            self.selection_start = self.camera.center_x, self.camera.center_y
            self.has_selection = False
        else:
            self.has_selection = True

    def _render_selection(self, window: pygame.Surface):
        """Draws the selection rectangle to the given window.

        Parameters
        ----------
        window : Surface
            The surface to render the selection to.
        """

        if len(self.selection) == 4:
            surf = pygame.Surface((self.selection[2], self.selection[3]), pygame.SRCALPHA)
            surf.fill(Builder.SELECTION_COLOUR, surf.get_rect())
            window.blit(
                surf,
                (
                    *self.camera.get_relative(self.selection[0], self.selection[1]),
                    self.selection[2],
                    self.selection[3],
                ),
            )

    def add_wall(self) -> None:
        """Adds the current selection to the map as a wall."""
        self.map.add_wall(Wall(*self.selection))

    def set_player(self) -> None:
        """Sets the map's player spawn to the current selection."""
        self.map.set_player(*self.selection)

    def handle_l_drag(self, curr_pos: Vec2) -> None:
        """Changes the selection based on the given position.

        Parameters
        ----------
        curr_pos : Position
            The current position of the mouse.
        """

        x_w_off, y_w_off = self.camera.get_absolute(*curr_pos)
        self.selection = normalise_rect(
            *self.selection_start,
            int(x_w_off - self.selection_start[0]),
            int(y_w_off - self.selection_start[1]),
        )

    def handle_r_drag(self, prev_pos: Vec2, curr_pos: Vec2) -> None:
        """Moves the camera by the difference between the current and previous mouse positions.

        Parameters
        ----------
        prev_pos : Position
            The position of the mouse in the previous tick.
        curr_pos : Position
            The current position of the mouse.
        """

        self.camera.move(prev_pos[0] - curr_pos[0], prev_pos[1] - curr_pos[1])
