import sys

import pygame

from src.hitbox import Hitbox
from src.map import Map
from src.map_builder.camera import Camera
from src.utils import normalise_rect


class Builder:
    SELECTION_COLOUR = 255, 255, 255, 120

    def __init__(self, window: pygame.Surface, zone: str, width: int, height: int):
        self.window = window
        self.map = Map(zone, load=False, width=width, height=height)
        self.camera = Camera(width, height)
        self.selection_start = ()
        self.selection = ()
        self.has_selection = False

    def main_loop(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000  # To get in seconds

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

            selection_changed = False
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
                self.selection = normalise_rect(*self.selection_start,
                                                int(self.camera.center_x - self.selection_start[0]),
                                                int(self.camera.center_y - self.selection_start[1]))

            self.window.fill((0, 0, 0))
            self.camera.render(self.window, self.map, render_fn=self._render_selection)
            pygame.display.update()

    def select(self) -> None:
        if len(self.selection_start) == 0 or self.has_selection:
            self.selection_start = self.camera.center_x, self.camera.center_y
            self.has_selection = False
        else:
            self.has_selection = True

    def _render_selection(self, window: pygame.Surface):
        if len(self.selection) == 4:
            surf = pygame.Surface((self.selection[2], self.selection[3]), pygame.SRCALPHA)
            surf.fill(Builder.SELECTION_COLOUR, surf.get_rect())
            window.blit(surf, (self.selection[0] - self.camera.x, self.selection[1] - self.camera.y,
                        self.selection[2], self.selection[3]))

    def add_wall(self):
        self.map.add_wall(Hitbox(*self.selection))
