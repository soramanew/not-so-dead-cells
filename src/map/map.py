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
from util.func import clamp, get_project_root
from util.type import Side

from .background import Background
from .corpse import Corpse
from .gate import Gate
from .platform import Platform
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

    SAFE_RANGE: int = 100

    @staticmethod
    def storage() -> Path:
        return get_project_root() / "assets/maps/ramparts"

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
            self.map_data = json.load(open(storage / "start.json"))
            texture = pygame.image.load(storage / "start.png")
            self.width: int = texture.width
            textures = [texture]

            i = 0
            segments = random.randint(4, 8)
            while i < segments or "gates" not in self.map_data:
                segment = random.choice([f for f in storage.iterdir() if f.is_file() and f.stem[0].isdigit()]).stem
                texture = pygame.image.load(storage / f"{segment}.png")
                textures.append(texture)

                map_data = json.load(open(storage / f"{segment}.json"))
                for prop in map_data:
                    for obj in map_data[prop]:
                        obj["bounds"][0] += self.width
                        if prop not in self.map_data:
                            self.map_data[prop] = []
                        self.map_data[prop].append(obj)

                self.width += texture.width
                i += 1

            # To simple namespace
            self.map_data = json.loads(json.dumps(self.map_data), object_hook=lambda d: SimpleNamespace(**d))

            # FIXME temp, change when have generated underground
            self.static_bg = False
            if self.static_bg:
                self.texture = pygame.Surface(texture.size).convert()
                self.texture.fill(self.map_data.background)
                self.texture.blit(texture, (0, 0))
            else:
                self.background: Background = Background()
                self.texture = pygame.Surface((self.width, textures[0].height), pygame.SRCALPHA).convert_alpha()
                off = 0
                for texture in textures:
                    self.texture.blit(texture, (off, 0))
                    off += texture.width

                # Bottom gradient
                surf = pygame.Surface((1, 2), pygame.SRCALPHA)
                pygame.draw.line(surf, (0, 0, 0), (0, 1), (1, 1))
                surf = pygame.transform.smoothscale(surf, (self.width, 500))
                self.texture.blit(surf, (0, self.texture.height - surf.height))

            # def gen_c() -> int:
            #     return random.randint(50, 255 // max(1, state.difficulty / 100))

            # tint = gen_c(), gen_c(), gen_c()
            # self.texture.fill(tint, special_flags=pygame.BLEND_MULT)
            # if self.static_bg:
            #     self.background: str = self.texture.get_at((0, 0))

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
            # Kill if out of map, TODO animation
            if enemy.top > self.height or enemy.death_finished:
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

    def player_out_of_bounds(self) -> None:
        # Damages player by 1/5 max health
        state.player.take_hit(state.player.max_health // 5, True)
        if state.player.health <= 0:
            return

        # Stop all actions
        state.player.interrupt_all()
        state.player.i_frames = 2  # A few seconds of i-frames

        x = state.player.center_x
        y = state.player.center_y

        walls = set()  # Walls already checked
        check_enemies = True

        while True:
            # TODO get nearest x by side if I can be bothered, cause currently this grabs by nearest center
            wall = self.get_nearest(x, self.height, lambda e: e not in walls and e in self.walls)
            walls.add(wall)

            # No matching wall
            if wall is None:
                if check_enemies:
                    print("[WARNING] Player out of bounds: no safe spawn area.")
                    check_enemies = False
                    walls.clear()
                    continue

                print("[CRITICAL] Player out of bounds: no suitable spawn area. Ignoring.")
                state.player.center_x = x
                state.player.center_y = y
                return

            bounds = wall.left + state.player.width / 2, wall.right - state.player.width / 2

            obstacles = self.get_rect(
                wall.x,
                wall.y - state.player.HEIGHT,
                wall.width,
                state.player.HEIGHT,  # Use max height, not current cause all actions are interrupted
                lambda e: e is not wall and e in self.walls or e in self.enemies,
            )

            # Get available positions to spawn
            spawns = clamp(x, bounds[1], bounds[0])
            spawns = [(abs(spawns - x), spawns, None)]
            for o in obstacles:
                off = state.player.width / 2 + (Map.SAFE_RANGE if o in self.enemies else 0)
                if bounds[0] < o.left - off < bounds[1]:
                    spawns.append((abs(o.left - x), o.left - off, o))
                if bounds[0] < o.right + off < bounds[1]:
                    spawns.append((abs(o.right - x), o.right + off, o))

            # Move to top of wall
            state.player.bottom = wall.top

            for _, pos, entity in sorted(spawns, key=lambda e: e[0]):
                state.player.center_x = pos
                # Return if found suitable position (no walls colliding + no enemies in safe range)
                if not (
                    self.get_rect(*state.player, lambda e: e is not wall and e in self.walls)
                    or (
                        check_enemies
                        and self.get_rect(
                            state.player.x - Map.SAFE_RANGE,
                            state.player.y - Map.SAFE_RANGE,
                            state.player.width + Map.SAFE_RANGE * 2,
                            state.player.height + Map.SAFE_RANGE * 2,
                            lambda e: e is not entity and e in self.enemies and not e.dead,
                        )
                    )
                ):
                    return

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
            self.add_wall(box)
            if hasattr(wall, "enemies"):
                # Random amount of enemies + more with higher difficulty
                for _ in range(floor(wall.enemies * random.uniform(0.8, 1.2) * (1 + state.difficulty / 10))):
                    self.spawn_enemy(box)
                # Random chance to spawn a corpse which weapons drop from
                if random.random() < 0.2:
                    self.add(Corpse(box))

        if hasattr(self.map_data, "platforms"):
            for platform in self.map_data.platforms:
                self.add_wall(Platform(*platform.bounds))

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
                if row >= 0 and row < self.rows and col >= 0 and col < self.cols:
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

        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
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

        clients = set()
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
                                    clients.add(c)
                        else:
                            clients |= cell

        return list(filter(filter_fn, clients)) if callable(filter_fn) else clients

    def get_nearest(self, x: float, y: float, filter_fn: type[Box] = None, max_depth: int = -1) -> Box | None:
        col = floor(x / self.cell_size)
        row = floor(y / self.cell_size)

        depth_cap = max(col, row, self.cols - col, self.rows - row)
        if max_depth < 0 or max_depth > depth_cap:
            max_depth = depth_cap

        depth = 1
        nearest = None
        nearest_d_sq = -1
        while nearest is None and depth <= max_depth:
            for i in range(-depth, depth + 1):
                r = row + i
                if r >= 0 and r < self.rows and self.grid[r] is not None:
                    for j in range(-depth, depth + 1):
                        if abs(i) >= depth or abs(j) >= depth:
                            c = col + j
                            if c >= 0 and c < self.cols:
                                cell = self.grid[r][c]
                                if cell is not None:
                                    for client in filter(filter_fn, cell) if callable(filter_fn) else cell:
                                        d_sq = (client.center_x - x) ** 2 + (client.center_y - y) ** 2
                                        if nearest_d_sq < 0 or d_sq < nearest_d_sq:
                                            nearest = client
                                            nearest_d_sq = d_sq

            depth += 1

        return nearest

    def add_wall(self, wall: Wall) -> None:
        """Adds the given wall into this map.

        This adds the wall to the walls array and the grid.

        Parameters
        ----------
        wall : Wall
            The wall to add.
        """

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
