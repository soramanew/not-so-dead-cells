from __future__ import annotations

import inspect
import json
import random
from collections.abc import Callable
from math import ceil, copysign, floor
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import state
from box import Box
from util.func import get_project_root
from util.type import Side

from .background import Background
from .wall import Wall

if TYPE_CHECKING:
    from enemy.enemy import Enemy
    from item import Pickup

    from .gate import Gate

type Cell = set[Box]
type Row = list[Cell | None]
type Grid = list[Row | None]


class Map:
    GRAVITY: int = 800
    AIR_RESISTANCE: float = 0.0003

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
        zone: str,
        load: bool = True,
        width: int = 2000,
        height: int = 2000,
        cell_size: int = 50,
    ) -> None:
        self.objects: set[Box] = set()
        self.zone = zone
        zone_dir = Map.storage() / self.zone

        if load:
            # self.save_path = random.choice(list(zone_dir.iterdir()))
            self.save_path = zone_dir / "1.json"
            map_data = json.load(open(self.save_path), object_hook=lambda d: SimpleNamespace(**d))
            self.width = int(map_data.width)
            self.height = int(map_data.height)
            self.cell_size = int(map_data.cell_size)
            self.init_dir = Side(map_data.init_dir)
            self.player_spawn = tuple(map_data.spawn)
        else:
            self.save_path = zone_dir / (str(int(max(zone_dir.iterdir()).stem) + 1) + ".json")
            self.width = width
            self.height = height
            self.cell_size = cell_size
            self.init_dir = Side.RIGHT
            self.player_spawn = (0, 0)

        self.rows = self.height // self.cell_size
        self.cols = self.width // self.cell_size
        self.grid: Grid = [None] * self.rows
        self.walls: set[Wall] = self._load_walls(map_data.walls) if load else set()
        self.enemies: set[Enemy] = set()
        self.pickups: set[Pickup] = set()
        self.gates: set[Gate] = set()
        self.background: Background = Background()

        # Reset player to default values, move to spawn and change facing to init dir
        state.player.to_default_values(*self.player_spawn, self.init_dir)

    def spawn_enemies(self):  # FIXME temp
        import enemy
        import item.weapon
        from item.pickup import (
            Apple,
            DamagePotion,
            HealthPotion,
            LemonPie,
            Sausages,
            Toe,
            WeaponPickup,
        )

        from .gate import Gate

        enemies = [cls for _, cls in inspect.getmembers(enemy) if inspect.isclass(cls)]
        weapons = [cls for _, cls in inspect.getmembers(item.weapon) if inspect.isclass(cls)]
        food_and_potions = [Apple, Toe, LemonPie, Sausages, DamagePotion, HealthPotion]
        for wall in self.walls:
            for i in range(1):
                enemy = random.choice(enemies)(wall)
                self.enemies.add(enemy)
                self.add(enemy)

            # Weapon = random.choice(weapons)
            # mods = [random.choice(Weapon.AVAILABLE_MODS)() for _ in range(random.randint(1, 3))]
            # pickup = WeaponPickup(Weapon(mods), wall)
            # self.pickups.add(pickup)
            # self.add(pickup)

            for i in range(3):
                food_or_potion = random.choice(food_and_potions)(wall)
                self.pickups.add(food_or_potion)
                self.add(food_or_potion)

            gate = Gate(random.uniform(wall.left, wall.right - 100), wall.top - 150, 100, 150)
            self.gates.add(gate)
            self.add(gate)

    def tick(self, dt: float) -> None:
        to_remove = set()
        for enemy in self.enemies:
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

        for pickup in self.pickups:
            self._remove(pickup, False)
            pickup.tick(dt)
            self._add(pickup, False)

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

    def _load_walls(self, walls: list[SimpleNamespace]) -> set[Wall]:
        """Loads the given walls into this map's spatial grid.

        This method loads each SimpleNamespace into a Wall, inserts it into the grid
        and returns the set of Walls.

        Parameters
        ----------
        walls : list of SimpleNamespace
            A list of walls to insert into the map.

        Returns
        -------
        set of Wall
            The set of walls as Walls.
        """

        wall_set = set()
        for wall in walls:
            box = Wall(float(wall.x), float(wall.y), int(wall.w), int(wall.h))
            wall_set.add(box)

        # Remove duplicates
        for wall in wall_set:
            self.add(wall)

        return wall_set

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
