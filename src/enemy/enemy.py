from map import Map
from wall import Wall
from .movement import EnemyMovement


class Enemy:
    def __init__(self, current_map: Map, platform: Wall, x: float, y: float, width: int, height: int, speed: float):
        self.movement: EnemyMovement = EnemyMovement(current_map, platform, x, y, width, height, speed)

    def tick(self, dt: float):
        self.movement.tick(dt)
