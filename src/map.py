import json
import math
import random
from types import SimpleNamespace

from src.hitbox import Hitbox
from src.utils import get_project_root


class Map:
    GRAVITY: int = 800
    FRICTION: float = 0.1
    AIR_RESISTANCE: float = 0.05

    def __init__(self, player, zone):
        self.player = player
        self.zone = zone

        map_data = json.load(open(random.choice(list((get_project_root() / f"assets/{zone}").iterdir()))),
                             object_hook=lambda d: SimpleNamespace(**d))
        self.width = int(map_data.width)
        self.height = int(map_data.height)
        self.cell_size = int(map_data.cell_size)
        self.rows = self.height // self.cell_size
        self.cols = self.width // self.cell_size
        self.grid: list[list[set[Hitbox] | None] | None] = [None] * self.rows
        self.walls = self._load_walls(map_data.walls)

        # TODO put default size, load from file or something, make level builder

    def _load_walls(self, walls):
        hitboxes = []
        for wall in walls:
            x = float(wall.x)
            y = float(wall.y)
            w = int(wall.w)
            h = int(wall.h)
            box = Hitbox(x, y, w, h)
            hitboxes.append(box)

            start_col = math.floor(x / self.cell_size)
            start_row = math.floor(y / self.cell_size)
            end_col = math.ceil((x + w) / self.cell_size)
            end_row = math.ceil((y + h) / self.cell_size)
            for row in range(start_row, end_row + 1):
                for col in range(start_col, end_col + 1):
                    self.insert_client(box, row, col)
        return hitboxes

    def insert_client(self, client, row, col):
        if self.grid[row] is None:
            self.grid[row] = [None] * self.cols
        if self.grid[row][col] is None:
            self.grid[row][col] = set()
        self.grid[row][col].add(client)

    def draw_debug(self, window):
        for wall in self.walls:
            wall.draw(window)
