import pygame
import state
from util.func import get_project_root


class Background:
    def __init__(self):
        width, height = pygame.display.get_window_size()
        self.width: int = width
        self.height: int = height

        self.orig_layers: list[pygame.Surface] = []
        self.layers: list[pygame.Surface] = []

        for layer in sorted((get_project_root() / "assets/background").iterdir()):
            layer = pygame.image.load(layer).convert()
            layer.set_colorkey((0, 0, 0), pygame.RLEACCEL)
            self.orig_layers.append(layer)
        self.orig_layers[0].set_colorkey(None, pygame.RLEACCEL)  # Base layer doesn't need alpha

        self.resize(width, height, override=True)

    def resize(self, width: int, height: int, override: bool = False) -> None:
        if not override and width == self.width and height == self.height:
            return

        self.width = width
        self.height = height

        height *= 1.5
        self.layers = [
            pygame.transform.scale_by(layer, (height / layer.height)) if height != layer.height else layer
            for layer in self.orig_layers
        ]

    def draw(self, surface: pygame.Surface) -> None:
        blits = []
        for idx, layer in enumerate(self.layers):
            x = (((state.current_map.width - state.camera.center_x) * idx) / 8) % layer.width
            if x > 0:
                x -= layer.width

            y = ((state.current_map.height - state.camera.bottom) * idx) / 16 - (layer.height - self.height) * 0.6

            while x < self.width:
                blits.append((layer, (x, y)))
                x += layer.width

        surface.blits(blits)
