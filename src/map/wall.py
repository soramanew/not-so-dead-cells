from box import Hitbox


class Wall(Hitbox):
    FRICTION: float = 0.1

    def draw(self, *args, **kwargs) -> None:
        # Ignore drawing, drawing is from map texture
        pass
