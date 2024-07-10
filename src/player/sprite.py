from pathlib import Path

import pygame
import state
from constants import SPRITES_PER_SECOND
from util.func import get_project_root
from util.type import Side

type SpriteDirectionList = list[pygame.Surface]
type SpriteList = tuple[SpriteDirectionList, SpriteDirectionList]  # Left, right

SPRITE_SIZE: int = 64


def _get_sprites_from_sheet(sheet: Path) -> SpriteList:
    sheet = pygame.image.load(sheet)

    sprites_right = []
    for i in range(sheet.width // SPRITE_SIZE):
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
        return int(self.time * SPRITES_PER_SECOND) % self.num_sprites

    @frame.setter
    def frame(self, value: int) -> None:
        self.time = value / SPRITES_PER_SECOND

    def __init__(self, sprites: SpriteList, speed: float = 1):
        self.sprites: SpriteList = sprites
        self.speed: float = speed
        self.num_sprites: int = len(sprites[0])
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


class PlayerSprite:
    @property
    def current_state(self) -> State:
        return self.states[state.player.state.value]

    @property
    def current_sprite(self) -> pygame.Surface:
        return self.current_state.get_current_sprite(state.player.facing)

    def __init__(self, folder: str):
        folder_path = get_project_root() / "assets/sprites" / folder
        self.states: dict[str, State] = {
            "attack": State(_get_sprites_from_sheet(folder_path / "Attack_1.png")),
            "dead": State(_get_sprites_from_sheet(folder_path / "Dead.png")),
            "idle": State(_get_sprites_from_sheet(folder_path / "Idle.png")),
            "walk": State(_get_sprites_from_sheet(folder_path / "Walk.png")),
            "sprint": State(_get_sprites_from_sheet(folder_path / "Sprint.png")),
            "jump": State(_get_sprites_from_sheet(folder_path / "Jump.png")),
            "climb": State(_get_sprites_from_sheet(folder_path / "Climb.png")),
            "wall_slide": State(_get_sprites_from_sheet(folder_path / "Wall_Slide.png")),
            "roll": State(_get_sprites_from_sheet(folder_path / "Roll.png"), 1.3),
            # "hurt": _get_sprites_from_sheet(folder_path / "Hurt.png")  # TODO stagger enemy and use when hurt
        }

        # self.death_time: float = 4  # Time remains stay for

    def tick(self, dt: float) -> None:
        # if self.dead:
        #     self.state = PlayerState.DEAD
        #     end = self.current_state.tick(dt, False)
        #     if end:
        #         self.death_time -= dt
        #     if self.death_time <= 0:
        #         self.death_finished = True
        # else:
        self.current_state.tick(dt)


class EffectSprite(State):
    def __init__(self, effect: str, x: float = None, y: float = None, once: bool = False, speed: float = 1):
        super().__init__(_get_sprites_from_sheet(get_project_root() / "assets/vfx" / f"{effect}.png"), speed)
        # Position for static
        self.x: float = x
        self.y: float = y
        # Only run once
        self.once: bool = once
        self.has_run: bool = False

    def tick(self, dt: float) -> bool:
        if self.once and self.has_run:
            return True

        end = super().tick(dt)
        if end:
            self.has_run = True
        return end
