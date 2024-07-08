from __future__ import annotations

import inspect
import json
import random
import time
from collections.abc import Callable
from math import ceil, copysign, floor
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pygame
import state
from box import Box
from util.func import get_project_root
from util.type import Side

from .background import Background
from .corpse import Corpse
from .gate import Gate
from .wall import Wall

if TYPE_CHECKING:
    from enemy.enemy import Enemy
    from item import Pickup

    from .effects import DamageNumber


type Cell = set[Box]
type Row = list[Cell | None]
type Grid = list[Row | None]

ENEMIES = None
WEAPONS = None


class Map:
    GRAVITY: int = 1000
    AIR_RESISTANCE: float = 0.0002

    @staticmethod
    def storage() -> Path:
        return get_project_root() / "assets/maps"

    @classmethod
    def get_air_resistance(cls, v: float, a: float) -> float:
        """Calculates air resistance based on the given velocity and area.

        Parameters
        ----------
        v : float
            The velocity.
        a : float
            The surface area.

        Returns
        -------
        float
            The air resistance.
        """
        return copysign((a * (cls.AIR_RESISTANCE * v**2) / 2), v)

    def __init__(
        self,
        load: bool = True,
        width: int = 2000,
        height: int = 2000,
        cell_size: int = 50,
    ) -> None:
        self.objects: set[Box] = set()
        storage = Map.storage()

        if load:
            chosen_map = random.choice([f for f in storage.iterdir() if f.is_file()]).stem
            texture = pygame.image.load(storage / f"{chosen_map}.png")
            self.map_data = json.load(open(storage / f"{chosen_map}.json"), object_hook=lambda d: SimpleNamespace(**d))
            self.static_bg = isinstance(self.map_data.background, str)
            if self.static_bg:
                self.texture = pygame.Surface(texture.size).convert()
                self.texture.fill(self.map_data.background)
                self.texture.blit(texture, (0, 0))
            else:
                self.texture = texture.convert_alpha()
                self.background: Background = Background()

            def gen_c() -> int:
                return random.randint(50, 255 // max(1, state.difficulty / 100))

            tint = gen_c(), gen_c(), gen_c()
            self.texture.fill(tint, special_flags=pygame.BLEND_MULT)
            if self.static_bg:
                self.background: str = self.texture.get_at((0, 0))

            self.width: int = self.texture.width
            self.height: int = self.texture.height
            self.cell_size: int = min(self.width, self.height) // 10

            # Reset player to default values, move to spawn and change facing to init dir
            state.player.to_default_values(*self.map_data.spawn, Side(self.map_data.init_dir))
            state.camera.instant_center()
        else:
            self.save_path = storage / (str(int(max(storage.iterdir()).stem) + 1) + ".json")
            self.width = width
            self.height = height
            self.cell_size = cell_size
            self.init_dir = Side.RIGHT
            self.player_spawn = (0, 0)

        self.rows: int = ceil(self.height / self.cell_size) + 1
        self.cols: int = ceil(self.width / self.cell_size) + 1
        self.grid: Grid = [None] * self.rows

        self.walls: set[Wall] = set()
        self.enemies: set[Enemy] = set()
        self.pickups: set[Pickup] = set()
        self.gates: set[Gate] = set()
        self.damage_numbers: set[DamageNumber] = set()

        # Lazy load enemy and weapon classes because cyclical imports
        global ENEMIES
        if ENEMIES is None:
            import enemy

            ENEMIES = [cls for _, cls in inspect.getmembers(enemy) if inspect.isclass(cls)]

        global WEAPONS
        if WEAPONS is None:
            import item.weapon

            WEAPONS = [cls for _, cls in inspect.getmembers(item.weapon) if inspect.isclass(cls)]

    def tick(self, dt: float) -> None:
        tick_bounds = state.camera.active_bounds
        to_remove = set()

        for enemy in self.get_rect(*tick_bounds, lambda e: e in self.enemies):
            self._remove(enemy, False)
            enemy.tick(dt)
            if enemy.death_finished:
                to_remove.add(enemy)
            else:
                self._add(enemy, False)
                if enemy.dead:
                    enemy.drop_loot()

        for enemy in to_remove:
            self.objects.remove(enemy)
            self.enemies.remove(enemy)

        for pickup in self.get_rect(*tick_bounds, lambda e: e in self.pickups):
            self._remove(pickup, False)
            pickup.tick(dt)
            self._add(pickup, False)

        to_remove = set()
        for dm in self.damage_numbers:
            self._remove(dm, False)
            remove = dm.tick(dt)
            if remove:
                to_remove.add(dm)
            else:
                self._add(dm, False)
        for dm in to_remove:
            self.objects.remove(dm)
            self.damage_numbers.remove(dm)

    def _to_cells(self, x: float, y: float, width: int, height: int) -> tuple[int, int, int, int]:
        """Converts the given rectangle to the cell coordinates of each side (left, top, right, bottom).

        Parameters
        ----------
        x : float
            The left-most x coordinate of the rectangle.
        y : float
            The top-most y coordinate of the rectangle.
        width : int
            The width of the rectangle.
        height : int
            The height of the rectangle.

        Returns
        -------
        tuple of int
            The coordinates of the left-most cell, top-most cell, right-most cell and bottom-most cell as a tuple.
        """

        return (
            floor(x / self.cell_size),
            floor(y / self.cell_size),
            ceil((x + width) / self.cell_size),
            ceil((y + height) / self.cell_size),
        )

    def load(self) -> None:
        start = time.process_time()

        for wall in self.map_data.walls:
            box = Wall(*wall.bounds)
            self.walls.add(box)
            self.add(box)
            if hasattr(wall, "enemies"):
                # Random amount of enemies + more with higher difficulty
                for _ in range(floor(wall.enemies * random.uniform(0.8, 1.2) * (1 + state.difficulty / 10))):
                    self.spawn_enemy(box)
                # Random chance to spawn a corpse which weapons drop from
                if random.random() < 0.2:
                    self.add(Corpse(box))

        for gate in self.map_data.gates:
            if not hasattr(gate, "optional") or not gate.optional or random.random() < 0.5:
                gate = Gate(*gate.bounds)
                self.gates.add(gate)
                self.add(gate)

        print(f"[DEBUG] Done loading map: took {(time.process_time() - start)*1000}ms")

    def add_damage_number(self, dm: DamageNumber) -> None:
        self.damage_numbers.add(dm)
        self.add(dm)

    def spawn_enemy(self, platform: Wall) -> None:
        enemy = random.choice(ENEMIES)(platform)
        self.enemies.add(enemy)
        self.add(enemy)

    def spawn_weapon(self, x: float, y: float) -> None:
        from item.pickup import WeaponPickup

        Weapon = random.choice(WEAPONS)
        mods = [random.choice(Weapon.AVAILABLE_MODS)() for _ in range(random.randint(1, 3))]
        self.add_pickup(WeaponPickup(Weapon(mods), (x, y)))

    def spawn_init_weapon(self) -> None:
        self.spawn_weapon(*self.map_data.init_weapon_pos)

    def remove_pickup(self, pickup: Pickup) -> None:
        self.remove(pickup)
        self.pickups.remove(pickup)

    def remove(self, box: Box) -> None:
        self._remove(box, True)

    def _remove(self, box: Box, remove_from_list: bool) -> None:
        if remove_from_list:
            self.objects.remove(box)
        start_col, start_row, end_col, end_row = self._to_cells(*box)
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                self.grid[row][col].remove(box)

    def add_pickups(self, pickups: list[Pickup]) -> None:
        for pickup in pickups:
            self.add_pickup(pickup)

    def add_pickup(self, pickup: Pickup) -> None:
        self.add(pickup)
        self.pickups.add(pickup)

    def add(self, box: Box) -> None:
        self._add(box, True)

    def _add(self, box: Box, add_to_list: bool) -> None:
        """Adds the given box to all cells in this map that intersect it.

        This method also adds the given box to this map's objects set.

        Parameters
        ----------
        box : Box
            The box to insert into this map.
        add_to_list : bool
            Whether to add the box to the objects list.
        """

        if add_to_list:
            self.objects.add(box)
        start_col, start_row, end_col, end_row = self._to_cells(*box)
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                self._add_to_cell(box, row, col)

    def _add_to_cell(self, client: Box, row: int, col: int) -> None:
        """Inserts a client (Box) into this map's spatial grid at the given position.

        This method should only be called from add_box().

        See Also
        --------
        add_box()

        Parameters
        ----------
        client : Box
            The client to insert into the map.
        row : int
            The row to insert the client into.
        col : int
            The column to insert the client into.
        """

        if row < 0 or row >= self.rows - 1 or col < 0 or col >= self.cols - 1:
            return

        if self.grid[row] is None:
            self.grid[row] = [None] * self.cols
        if self.grid[row][col] is None:
            self.grid[row][col] = set()
        self.grid[row][col].add(client)

    def get_rect(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        filter_fn: Callable[[Box], bool] = None,
        precision: bool = True,
    ) -> list[Box]:
        """Fetches all clients in this map within the given rectangle.

        Parameters
        ----------
        x : float
            The left-most x coordinate of the rectangle to search in.
        y : float
            The top-most y coordinate of the rectangle to search in.
        width : int
            The width of the rectangle to search in.
        height : int
            The height of the rectangle to search in.
        filter_fn : callable with parameters [Box] and return bool, optional
            A function to filter for specific clients.
        precision : bool, default True
            Whether to check for precise bounds or just use spatial hash columns

        Returns
        -------
        list of Box
            A list of clients in this map within the given rectangle.
        """

        clients = []
        s_col, s_row, e_col, e_row = self._to_cells(x, y, width, height)
        if s_row < 0:
            s_row = 0
        if e_row >= self.rows:
            e_row = self.rows
        if s_col < 0:
            s_col = 0
        if e_col >= self.cols:
            e_col = self.cols

        for row in range(s_row, e_row):
            if self.grid[row] is not None:
                for col in range(s_col, e_col):
                    cell = self.grid[row][col]
                    if cell is not None:
                        if precision:
                            for c in cell:
                                if x < c.right and x + width > c.left and y < c.bottom and y + height > c.top:
                                    clients.append(c)
                        else:
                            clients += cell

        return list(filter(filter_fn, set(clients))) if callable(filter_fn) else clients

    def add_wall(self, wall: Wall) -> None:
        """Adds the given wall into this map.

        This adds the wall to the walls array and the grid.

        Parameters
        ----------
        wall : Wall
            The wall to add.
        """

        if wall not in self.walls:
            self.walls.add(wall)
            self.add(wall)

    def set_player_spawn(self, x: float, y: float, width: int, height: int) -> None:
        """Sets the player spawn for this map.

        This also determines the size of the player.

        Parameters
        ----------
        x : float
            The left-most position of the player spawn.
        y : float
            The top-most position of the player spawn.
        width : int
         The width of the player spawn.
        height : int
            The height of the player spawn.
        """

        self.player_spawn = (x, y, width, height)
        self.init_dir = Side.LEFT if width < 0 else Side.RIGHT

    def save(self) -> dict[str, Any]:
        """Saves this map as a JSON file and returns the JSON object representation.

        See Also
        --------
        Box.to_json()

        Returns
        -------
        dict with str key and any value
            The JSON representation of this map.
        """

        json_obj = {
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "spawn": self.player_spawn,
            "init_dir": self.init_dir.value,
            "walls": [wall.to_json() for wall in self.walls],
        }

        with open(self.save_path, "w") as file:
            file.write(json.dumps(json_obj))

        return json_obj
