import pygame
from util.func import get_project_root


class Background:
    def __init__(self):
        width, height = pygame.display.get_window_size()
        self.width: int = width
        self.height: int = height

        self.x: float = 0
        self.y: float = 0
        self.off: float = 0

        self.orig_layers: list[pygame.Surface] = []
        self.layers: list[pygame.Surface] = []
        self.offsets: list[float] = []

        for layer in sorted((get_project_root() / "assets/background").iterdir()):
            self.orig_layers.append(pygame.image.load(layer).convert_alpha())
            self.offsets.append(0)
        self.orig_layers[0] = self.orig_layers[0].convert()  # Base layer doesn't need alpha
        self.num_layers: int = len(self.orig_layers)
        self.max_off: float = self.orig_layers[0].height * 0.1

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

    def tick(self, dx: float, dy: float) -> None:
        self.x -= dx / 8
        self.y -= dy / 160

    def draw(self, surface: pygame.Surface) -> None:
        blits = []
        for idx, layer in enumerate(self.layers):
            x = (self.x * idx) % layer.width
            if x > 0:
                x -= layer.width

            y = self.y * idx

            while x < self.width:
                blits.append((layer, (x, y - (layer.height - self.height) * 0.6)))
                x += layer.width

        surface.blits(blits)
