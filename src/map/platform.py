import state
from box import Box

from .wall import Wall


class Platform(Wall):
    def detect_collision(self, left: float, top: float, right: float, bottom: float, player: bool = False) -> bool:
        if player:
            if state.player.vy < 0:
                state.player.should_not_collide.add(self)
                return False
            if self in state.player.should_not_collide:
                return False
        return self.left < right and self.right > left and self.top < bottom and self.bottom > top

    def detect_collision_box(self, box: Box) -> bool:
        return self.detect_collision(box.left, box.top, box.right, box.bottom, box is state.player)
