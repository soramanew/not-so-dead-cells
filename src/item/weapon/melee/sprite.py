from pathlib import Path

import pygame
from constants import SPRITES_PER_SECOND
from util.func import get_project_root
from util.type import Side

type SpriteDirectionList = list[pygame.Surface]
type SpriteList = tuple[SpriteDirectionList, SpriteDirectionList]  # Left, right


def _get_sprites_from_sheet(sheet: Path, num_frames: int) -> SpriteList:
    sheet = pygame.image.load(sheet)
    width = sheet.width // num_frames
    height = sheet.height

    sprites_right = []
    for i in range(num_frames):
        sprite = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
        sprite.blit(sheet, (0, 0), (width * i, 0, width, height))
        sprites_right.append(sprite)

    sprites_left = []
    for sprite in sprites_right:
        sprites_left.append(pygame.transform.flip(sprite, True, False))

    return sprites_left, sprites_right


class Sprite:
    @property
    def frame(self) -> int:
        return int(self.time * SPRITES_PER_SECOND) % self.num_sprites

    @frame.setter
    def frame(self, value: int) -> None:
        self.time = value / SPRITES_PER_SECOND

    def __init__(self, sprite: str, num_frames: int, speed: float = 1):
        self.sprites: SpriteList = _get_sprites_from_sheet(
            get_project_root() / f"assets/sprites/{sprite}.png", num_frames
        )
        self.speed: float = speed
        self.num_sprites: int = num_frames
        self.time: float = 0

    def get_current_sprite(self, facing: Side) -> pygame.Surface:
        return self.sprites[0 if facing is Side.LEFT else 1][self.frame]

    def tick(self, dt: float, loop: bool = True) -> bool:
        """Ticks this state's animation.

        Parameters
        ----------
        dt : float
            The time between this tick and the last.
        loop : bool, default = True
            Whether to loop back to the start if finished with the animation.

        Returns
        -------
        bool
            If the animation is at the end.
        """

        self.time += dt * self.speed
        if self.frame >= self.num_sprites:
            if loop:
                self.time -= self.num_sprites / SPRITES_PER_SECOND
            else:
                # Set to last frame
                self.time = (self.num_sprites - 1) / SPRITES_PER_SECOND
        return self.frame >= self.num_sprites - 1
