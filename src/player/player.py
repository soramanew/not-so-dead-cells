from map import Map
from util_types import PlayerControl
from .movement import PlayerMovement


class Player:
    def __init__(self, current_map: Map, x: float, y: float, width: int = 10, height: int = 30):
        self.movement = PlayerMovement(current_map, x, y, width, height)  # This is position & size

    def tick(self, dt: float, moves: list[PlayerControl]) -> None:
        self.movement.handle_moves(dt, *moves)
        self.movement.tick_changes(dt)
        collisions = self.movement.update_position(dt)
        self.movement.handle_collisions(collisions)
