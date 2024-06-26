from pathlib import Path

import pygame
from util.func import get_project_root
from util.type import EnemyState, Side

from .enemyabc import EnemyABC

type SpriteDirectionList = list[pygame.Surface]
type SpriteList = tuple[SpriteDirectionList, SpriteDirectionList]  # Left, right

SPRITE_SIZE: int = 128
SPRITES_PER_SECOND: int = 10


def _get_sprites_from_sheet(sheet: Path) -> SpriteList:
    sheet = pygame.image.load(sheet)

    sprites_right = []
    for i in range(sheet.width // 128):
        sprite = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA).convert_alpha()
        sprite.blit(sheet, (0, 0), (SPRITE_SIZE * i, 0, SPRITE_SIZE, SPRITE_SIZE))
        sprites_right.append(sprite)

    sprites_left = []
    for sprite in sprites_right:
        sprites_left.append(pygame.transform.flip(sprite, True, False))

    return sprites_left, sprites_right


class State:
    @property
    def frame(self) -> int:
        return int(self.time * SPRITES_PER_SECOND)

    def __init__(self, sprites: SpriteList):
        self.sprites: SpriteList = sprites
        self.num_sprites: int = len(sprites[0])
        self.time: float = 0

    def current_sprite(self, facing: Side) -> pygame.Surface:
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

        self.time += dt
        if self.frame >= self.num_sprites:
            if loop:
                self.time -= self.num_sprites / SPRITES_PER_SECOND
            else:
                self.time = (self.num_sprites - 1) / SPRITES_PER_SECOND
        return self.frame >= self.num_sprites - 1


class Sprite(EnemyABC, pygame.sprite.Sprite):
    @property
    def current_state(self) -> State:
        return self.states[self.state.value]

    @property
    def current_sprite(self) -> pygame.Surface:
        return self.current_state.current_sprite(self.facing)

    def __init__(self, folder: str, state: EnemyState = EnemyState.IDLE, **kwargs):
        folder_path = get_project_root() / "assets/sprites" / folder
        self.states: dict[str, State] = {
            "attack": State(_get_sprites_from_sheet(folder_path / "Attack_1.png")),
            "dead": State(_get_sprites_from_sheet(folder_path / "Dead.png")),
            "idle": State(_get_sprites_from_sheet(folder_path / "Idle.png")),
            "walk": State(_get_sprites_from_sheet(folder_path / "Walk.png")),
            # "hurt": _get_sprites_from_sheet(folder_path / "Hurt.png")  # TODO stagger enemy and use when hurt
        }

        super().__init__(**kwargs)
        self.state: EnemyState = state

        self.death_time: float = 4  # Time remains stay for

    def _tick_sprite(self, dt: float) -> None:
        if self.dead:
            self.state = EnemyState.DEAD
            end = self.current_state.tick(dt, False)
            if end:
                self.death_time -= dt
            if self.death_time <= 0:
                self.death_finished = True
        else:
            self.current_state.tick(dt)
