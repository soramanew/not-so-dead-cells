from .enemy import Enemy


class EnemySense:
    """The sensing area of an Enemy. This is a sector of a circle."""

    def __init__(
        self,
        parent: Enemy,
        width: float,
        height: float,
        angle: float,
        xray: bool = False,
        x: float = None,
        y: float = None,
    ):
        if x is None:
            x = self.parent._head_x
        if y is None:
            y = self.parent.head_y

        self.parent: Enemy = parent  # The Enemy this belongs to
        self.width: float = width  # The length of the sense area
        self.height: float = height  # The height of the sense area
        self.angle: float = angle  # The angle the sense area makes with the horizontal
        self.xray: bool = xray  # If the sense goes through walls
        self.x: float = x
        self.y: float = y

    def check_for_player(self):
        # TODO
        pass
