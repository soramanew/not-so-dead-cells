import math
import random

import config
import pygame
import state
from camera import Camera
from map import Map
from player import Player
from util import key_handler
from util.func import change_music, clamp, get_font, get_fps, get_project_root
from util.type import Colour, PlayerControl, Side, Sound, Vec2


class ShadowTextButton(pygame.Rect):
    @property
    def clicked(self) -> bool:
        return self._clicked

    @clicked.setter
    def clicked(self, value: bool) -> None:
        if self._clicked == value:
            return

        self._clicked = value

        click_diff = (self.shadow_off - self.shadow_off_clicked) * (1 if value else -1)
        self.x += click_diff
        self.y += click_diff

        self.update()

    @property
    def font(self) -> pygame.font.Font:
        return self._font

    @font.setter
    def font(self, value: pygame.font.Font) -> None:
        self._font = value
        self.update()

    @property
    def hovered(self) -> bool:
        return self._hovered

    @hovered.setter
    def hovered(self, value: bool) -> None:
        if self._hovered == value:
            return

        self._hovered = value
        self.update()

    @property
    def text(self) -> pygame.Surface:
        return self._text

    @text.setter
    def text(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._text = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        self._text.blit(value, (0, 0), rect)
        self.size = self._text.size

    @property
    def shadow(self) -> pygame.Surface:
        return self._shadow

    @shadow.setter
    def shadow(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._shadow = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        self._shadow.blit(value, (0, 0), rect)

    def __init__(
        self,
        font: pygame.font.Font,
        text: str,
        colour: Colour,
        depth: float = 1 / 15,
        clicked_depth: float = 0.7,
        wrap_length: int = 0,
    ):
        self._font: pygame.font.Font = font
        self.text_str: str = text
        self.colour: Colour = colour
        r, g, b = colour
        self.hover_colour: Colour = r * 0.9, g * 0.9, b * 0.9
        self.shadow_colour: Colour = r * 0.1, g * 0.1, b * 0.1
        self.shadow_off: Vec2 = 1 + font.point_size * depth
        self.shadow_off_clicked: Vec2 = self.shadow_off * clicked_depth
        self.wrap_length: int = wrap_length

        self._text: pygame.Surface = None
        self._shadow: pygame.Surface = None
        self._clicked: bool = False
        self._hovered: bool = False

        self.update()
        super().__init__(0, 0, self.text.width, self.text.height)

    def update(self) -> None:
        self.text = self.font.render(
            self.text_str, True, self.hover_colour if self.hovered else self.colour, wraplength=self.wrap_length
        )
        self.shadow = self.font.render(self.text_str, True, self.shadow_colour, wraplength=self.wrap_length)

    def draw(self, surface: pygame.Surface) -> None:
        shadow_off = self.shadow_off_clicked if self.clicked else self.shadow_off
        surface.blit(self.shadow, (self.x + shadow_off, self.y + shadow_off))
        surface.blit(self.text, self.topleft)


class Checkbox(ShadowTextButton):
    SPACING: float = 0.4
    THICKNESS: float = 0.2
    INNER_SPACING: float = 0.14

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        self._checked = value
        self.update()

    @property
    def text(self) -> pygame.Surface:
        return self._text

    @text.setter
    def text(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._text = pygame.Surface(
            (rect.width + rect.height * (1 + Checkbox.SPACING), rect.height), pygame.SRCALPHA
        ).convert_alpha()
        self._text.blit(value, (0, 0), rect)
        colour = self.hover_colour if self.hovered else self.colour
        thickness = int(rect.height * Checkbox.THICKNESS)
        inner_gap = thickness + int(rect.height * Checkbox.INNER_SPACING)
        x = rect.width + int(rect.height * Checkbox.SPACING)
        pygame.draw.rect(self._text, colour, (x, 0, rect.height, rect.height), width=thickness)
        if self.checked:
            pygame.draw.rect(
                self._text,
                colour,
                (x + inner_gap, inner_gap, rect.height - inner_gap * 2, rect.height - inner_gap * 2),
            )
        self.size = self._text.size

    @property
    def shadow(self) -> pygame.Surface:
        return self._shadow

    @shadow.setter
    def shadow(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._shadow = pygame.Surface(
            (rect.width + rect.height * (1 + Checkbox.SPACING), rect.height), pygame.SRCALPHA
        ).convert_alpha()
        self._shadow.blit(value, (0, 0), rect)
        thickness = int(rect.height * Checkbox.THICKNESS)
        inner_gap = thickness + int(rect.height * Checkbox.INNER_SPACING)
        x = rect.width + int(rect.height * Checkbox.SPACING)
        pygame.draw.rect(self._shadow, self.shadow_colour, (x, 0, rect.height, rect.height), width=thickness)
        if self.checked:
            pygame.draw.rect(
                self._shadow,
                self.shadow_colour,
                (x + inner_gap, inner_gap, rect.height - inner_gap * 2, rect.height - inner_gap * 2),
            )

    @ShadowTextButton.clicked.setter
    def clicked(self, value: bool) -> None:
        if self._clicked == value:
            return

        self._clicked = value

        click_diff = (self.shadow_off - self.shadow_off_clicked) * (1 if value else -1)
        self.x += click_diff
        self.y += click_diff

        if value != self.on_release:
            self.checked = not self.checked

    def __init__(
        self,
        font: pygame.font.Font,
        text: str,
        colour: Colour,
        depth: float = 1 / 15,
        clicked_depth: float = 0.7,
        wrap_length: int = 0,
        checked: bool = False,
        side: Side = Side.RIGHT,
        on_release: bool = False,
    ):
        self._checked: bool = checked
        self.side: Side = side
        self.on_release: bool = on_release
        super().__init__(font, text, colour, depth, clicked_depth, wrap_length)


class Screen:
    def __init__(self, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        self.window: pygame.Surface = window
        self.clock: pygame.Clock = clock
        self.fps_cap: int = fps_cap or get_fps()

        self.exit: bool = False
        self.dt: float = 0
        self.skip_frames: int = 0

    def init_loop(self) -> None:
        self.exit = False
        self.on_resize(*self.window.size)

    def main_loop(self) -> bool:
        self.init_loop()

        while True:
            self.dt = self.clock.tick(self.fps_cap) / 1000  # To get in seconds

            self.pre_event_handling()

            if self.skip_frames > 0:
                self.skip_frames -= 1
                continue

            for event in pygame.event.get():
                if self.handle_event(event):
                    return True

            if self.exit:
                return

            if self.tick():
                return True

            self.draw()
            pygame.display.flip()

    def handle_event(self, event: pygame.Event) -> bool:
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.key == pygame.K_m and pygame.key.get_mods() & pygame.KMOD_CTRL:
                config.muted = not config.muted
        elif event.type == pygame.VIDEORESIZE:
            self.on_resize(*event.dict["size"])

    def on_resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def pre_event_handling(self) -> None:
        pass

    def tick(self) -> bool:
        pass

    def draw(self) -> None:
        pass


class DeathScreen(Screen):
    def handle_event(self, event: pygame.Event) -> bool:
        if super().handle_event(event):
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.exit = True
            return

    def init_loop(self) -> None:
        super().init_loop()

        change_music("game_over", "ogg")

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        death_text = get_font("Sabo", width // 15).render("You Died.", True, (255, 255, 255))
        self.death_text = death_text, ((width - death_text.width) / 2, (height - death_text.height) / 2)

        score = get_font("PixelifySans", width // 45).render(f"Score: {state.score}", True, (255, 255, 255))
        self.score = score, ((width - score.width) / 2, height * 0.6 - score.height / 2)

        prompt = get_font("Silkscreen", width // 45).render("Click anywhere to exit", True, (255, 255, 255))
        self.prompt = prompt, ((width - prompt.width) / 2, height * 0.8 - prompt.height / 2)

    def draw(self) -> None:
        intensity = 255 * max(0, 1 - self.dt)
        self.window.fill((255, intensity, intensity), special_flags=pygame.BLEND_MULT)
        surface = pygame.transform.gaussian_blur(self.window, clamp(int(10 * self.dt), 10, 1))
        self.window.blit(surface, (0, 0))

        self.window.blit(*self.death_text)
        self.window.blit(*self.score)
        self.window.blit(*self.prompt)


class Game(Screen):
    def create_h_bar(self, width: int, height: int) -> None:
        h_bar_height = height * 0.04
        x, y, w, h = 50, height - h_bar_height - 50, width * 0.33, h_bar_height

        # Base
        self.h_bar = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
        pygame.draw.rect(self.h_bar, (0, 0, 0, 100), (x, y, w, h), border_radius=3)

        # Inner
        i_w = 0.97  # inner width
        i_h = 0.7  # inner height
        self.h_bar_inner_rect = x + w * (1 - i_w) / 2, y + h * (1 - i_h) / 2, w * i_w, h * i_h
        pygame.draw.rect(self.h_bar, (82, 191, 118), self.h_bar_inner_rect, width=1, border_radius=10)

        self.h_bar_font = get_font("BIT", int(height * 0.02))

    def create_damage_tint(self, width: int, height: int, strength: int, size: int = 5) -> pygame.Surface:
        strength = 255 - strength
        surface = pygame.Surface((size, size)).convert()
        surface.fill((255, 255, 255))
        pygame.draw.rect(surface, (255, strength, strength), (0, 0, size, size), width=1)
        return pygame.transform.smoothscale(surface, (width, height))

    def create_damage_tints(self, width: int, height: int, start: int = 1, stop: int = 255, step: int = 25) -> None:
        self.damage_tints = [self.create_damage_tint(width, height, i) for i in range(start, stop, step)]
        self.max_damage_tint = len(self.damage_tints) - 1

    def __init__(self, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(window, clock, fps_cap)

        self.enter_map_sfx = Sound(get_project_root() / "assets/sfx/Enter_Level.wav")

    def init_loop(self) -> None:
        state.reset()
        key_handler.reset()

        state.player = Player()
        state.camera = Camera()
        state.current_map = Map()

        state.current_map.spawn_init_weapon()

        self.paused = False
        self.skip_frame = False
        self.back_confirm = False
        self.need_update = False

        super().init_loop()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        state.camera.resize(width, height)
        if not state.current_map.static_bg:
            state.current_map.background.resize(width, height)

        self.create_h_bar(width, height)
        self.create_damage_tints(width, height)

        self.overlay_font = get_font("Silkscreen", width // 60)
        self.title_font = get_font("SilkscreenExpanded", width // 10, "Bold")
        self.top_pause_font = get_font("PixelifySans", width // 30)
        self.bottom_pause_font = get_font("PixelifySans", width // 40)
        prompt_font = get_font("Silkscreen", width // 45)
        self.pause_prompts = [
            prompt_font.render("[Esc] to resume", True, (255, 255, 255)),
            prompt_font.render("[B] to return to the main menu", True, (255, 255, 255)),
        ]
        self.back_prompts = [
            prompt_font.render("[Esc] Nooooo, let me keep playing!", True, (255, 255, 255)),
            prompt_font.render("[B] I want to leave, LET ME OUT!!!", True, (255, 255, 255)),
        ]

        self.need_update = True

    def pre_event_handling(self) -> None:
        if not state.map_loaded:
            change_music("pause")

            # Loading screen
            self.window.fill((0, 0, 0))
            text = get_font("Sabo", self.width // 15).render("Loading...", True, (255, 255, 255))
            self.window.blit(text, ((self.width - text.width) / 2, (self.height - text.height) / 2))
            pygame.display.flip()

            state.current_map.load()
            state.map_loaded = True
            self.skip_frames = 2  # Skip this and the next frame so the loading time doesn't count as dt
            self.enter_map_sfx.play()
            change_music("game", "ogg", random.uniform(0, 90))

        self.moves = []
        if key_handler.get(pygame.K_LEFT) or key_handler.get(pygame.K_a):
            self.moves.append(PlayerControl.LEFT)
        if key_handler.get(pygame.K_RIGHT) or key_handler.get(pygame.K_d):
            self.moves.append(PlayerControl.RIGHT)

    def handle_event(self, event: pygame.Event) -> bool:
        if super().handle_event(event):
            return True
        elif event.type == pygame.KEYDOWN:
            # TODO changeable keybinds
            key_handler.down(event.key)
            jump = event.key == pygame.K_w or event.key == pygame.K_UP or event.key == pygame.K_SPACE
            if (key_handler.get(pygame.K_s) or key_handler.get(pygame.K_DOWN)) and jump:
                self.moves.append(PlayerControl.SLAM)
            elif jump:
                self.moves.append(PlayerControl.JUMP)
            elif event.key == pygame.K_f:
                self.moves.append(PlayerControl.INTERACT)
            elif event.key == pygame.K_COMMA:
                self.moves.append(PlayerControl.ATTACK_START)
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                state.player.sprinting = True
            elif event.key == pygame.K_ESCAPE:
                if self.back_confirm:
                    self.back_confirm = False
                else:
                    self.paused = not self.paused
                if self.paused:
                    change_music("pause")
                    pygame.mixer.pause()
                else:
                    change_music("game", "ogg", random.uniform(0, 90))
                    pygame.mixer.unpause()
                self.need_update = True
            elif event.key == pygame.K_b:
                if self.back_confirm:
                    self.exit = True
                    return
                change_music("pause")
                pygame.mixer.pause()
                self.back_confirm = True
                self.need_update = True
        elif event.type == pygame.KEYUP:
            held_time = key_handler.up(event.key)
            if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                if held_time < key_handler.TAP_THRESHOLD:
                    self.moves.append(PlayerControl.ROLL)
                state.player.sprinting = False
            elif event.key == pygame.K_COMMA:
                self.moves.append(PlayerControl.ATTACK_STOP)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.moves.append(PlayerControl.ATTACK_START)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.moves.append(PlayerControl.ATTACK_STOP)

    def tick(self) -> bool:
        if not (self.paused or self.back_confirm):
            key_handler.tick(self.dt)
            state.player.tick(self.dt, self.moves)
            if state.player.top > state.current_map.height:
                state.current_map.player_out_of_bounds()
            if state.player.health <= 0:
                full_exit = DeathScreen(self.window, self.clock).main_loop()
                if state.hardcore:
                    import platform
                    import subprocess

                    # NOTE Shuts down the PC
                    if platform.system() == "Windows":
                        subprocess.run(["shutdown", "-s"])
                    elif platform.system() == "Linux":
                        subprocess.run(["shutdown"])
                    else:
                        subprocess.call(["osascript", "-e", 'tell app "System Events" to shut down'])
                self.exit = True
                return full_exit
            state.current_map.tick(self.dt)
            state.camera.tick_move(self.dt)

    def draw_damage_tint(self) -> None:
        if 0 <= state.player.health <= state.player.max_health * 0.2:
            # Low health tint
            self.window.blit(
                self.damage_tints[
                    int((1 - state.player.health / (state.player.max_health * 0.5)) * self.max_damage_tint)
                ],
                (0, 0),
                special_flags=pygame.BLEND_MULT,
            )
        elif state.player.damage_tint_time > 0:
            # Damage flash
            self.window.blit(
                self.damage_tints[
                    int(
                        math.sin(math.pi * (state.player.damage_tint_time / state.player.damage_tint_init_time))
                        * (self.max_damage_tint / 2)
                    )
                ],
                (0, 0),
                special_flags=pygame.BLEND_MULT,
            )

    def draw_overlay_text(self) -> None:
        # FPS
        fps = self.overlay_font.render(f"FPS: {round(self.clock.get_fps(), 2)}", True, (255, 255, 255))
        self.window.blit(fps, (15, 15))

        # Score
        self.window.blit(
            self.overlay_font.render(f"Score: {state.score}", True, (255, 255, 255)), (15, 15 + fps.height)
        )

        # Multipliers (damage, health)
        multipliers = self.overlay_font.render(
            f"Damage x{round(state.player.damage_mul, 2)}, Health x{round(state.player.health_mul, 2)}",
            True,
            (255, 255, 255),
        )
        self.window.blit(multipliers, (self.width - 15 - multipliers.width, self.height - 15 - multipliers.height))

    def draw_health_bar(self):
        # Draw GUI
        self.window.blit(self.h_bar, (0, 0))  # Health bar base
        # Health bar health gain opportunity
        border = 0 if state.player.health < state.player.max_health else -1
        if state.player.damage_health >= 1:
            pygame.draw.rect(
                self.window,
                (213, 162, 59),
                (
                    self.h_bar_inner_rect[0],
                    self.h_bar_inner_rect[1],
                    self.h_bar_inner_rect[2]
                    * ((state.player.health + state.player.damage_health) / state.player.max_health),
                    self.h_bar_inner_rect[3],
                ),
                border_radius=10,
                border_top_right_radius=border,
                border_bottom_right_radius=border,
            )
        # Actual health
        border = 0 if state.player.health + state.player.damage_health < state.player.max_health else -1
        pygame.draw.rect(
            self.window,
            (82, 191, 118),
            (
                self.h_bar_inner_rect[0],
                self.h_bar_inner_rect[1],
                self.h_bar_inner_rect[2] * (state.player.health / state.player.max_health),
                self.h_bar_inner_rect[3],
            ),
            border_radius=10,
            border_top_right_radius=border,
            border_bottom_right_radius=border,
        )
        # Health text
        health_text_uncropped = self.h_bar_font.render(
            f"{state.player.health} / {state.player.max_health}", True, (255, 255, 255)
        )
        health_text_rect = health_text_uncropped.get_bounding_rect()
        player_health = pygame.Surface(health_text_rect.size, pygame.SRCALPHA)
        player_health.blit(health_text_uncropped, (0, 0), health_text_rect)
        self.window.blit(
            player_health,
            (
                self.h_bar_inner_rect[0] + (self.h_bar_inner_rect[2] - player_health.width) / 2,
                self.h_bar_inner_rect[1] + (self.h_bar_inner_rect[3] - player_health.height) / 2,
            ),
        )

    def draw(self) -> None:
        if self.need_update or not (self.paused or self.back_confirm):
            # Draw stuff
            state.camera.render(self.window)

            self.draw_damage_tint()
            self.draw_overlay_text()
            self.draw_health_bar()

        if self.need_update and (self.back_confirm or self.paused):
            # Darken and blur
            self.window.fill((140, 140, 140), special_flags=pygame.BLEND_MULT)
            surface = pygame.transform.gaussian_blur(self.window, 10)

            if self.back_confirm:
                # Question
                confirm = self.title_font.render("Really?", True, (255, 255, 255))
                y_off = (surface.height - confirm.height) / 2
                surface.blit(confirm, ((surface.width - confirm.width) / 2, y_off))

                # Prompts
                height = sum([p.height for p in self.back_prompts])
                for i, prompt in enumerate(self.back_prompts):
                    surface.blit(
                        prompt,
                        (
                            (surface.width - prompt.width) / 2,
                            (y_off + confirm.height) * 1.3
                            - height / 2
                            + (sum(p.height for p in self.back_prompts[:i]) if i > 0 else 0),
                        ),
                    )
            else:
                # Centered pause text
                pause_text = self.title_font.render("PAUSED", True, (255, 255, 255))
                y_off = (self.height - pause_text.height) / 2
                surface.blit(pause_text, ((self.width - pause_text.width) / 2, y_off))

                # Score and difficulty
                score = self.top_pause_font.render(f"Current score: {state.score}  ", True, (255, 255, 255))
                surface.blit(score, (self.width / 2 - score.width - 10, y_off * 0.8 - score.height / 2))
                separator = self.top_pause_font.render("|", True, (255, 255, 255))
                surface.blit(separator, (self.width / 2 - separator.width, y_off * 0.8 - separator.height / 2))
                difficulty = self.top_pause_font.render(
                    f" Current difficulty: {round(state.difficulty, 2)}x", True, (255, 255, 255)
                )
                surface.blit(difficulty, (self.width / 2 + 10, y_off * 0.8 - difficulty.height / 2))

                # Multipliers
                damage = self.bottom_pause_font.render(
                    f"Damage multiplier: {round(state.player.damage_mul, 2)}x  ", True, (255, 255, 255)
                )
                surface.blit(
                    damage,
                    (self.width / 2 - damage.width - 10, (y_off + pause_text.height) * 1.1 - damage.height / 2),
                )
                separator = self.bottom_pause_font.render("|", True, (255, 255, 255))
                surface.blit(
                    separator,
                    (self.width / 2 - separator.width, (y_off + pause_text.height) * 1.1 - separator.height / 2),
                )
                health = self.bottom_pause_font.render(
                    f" Health multiplier: {round(state.player.health_mul, 2)}x", True, (255, 255, 255)
                )
                surface.blit(health, (self.width / 2 + 10, (y_off + pause_text.height) * 1.1 - health.height / 2))

                height = sum([p.height for p in self.pause_prompts])
                for i, prompt in enumerate(self.pause_prompts):
                    surface.blit(
                        prompt,
                        (
                            (self.width - prompt.width) / 2,
                            (y_off + pause_text.height) * 1.3
                            - height / 2
                            + (sum(p.height for p in self.pause_prompts[:i]) if i > 0 else 0),
                        ),
                    )

                if state.player.weapon:
                    weapon = state.player.weapon
                    font = get_font("Silkscreen", self.width // 60)
                    name = get_font("BIT", self.width // 50).render(weapon.name, True, (255, 255, 255))
                    dps = font.render(f"{weapon.dps} DPS", True, (180, 180, 180))
                    mods = font.render(weapon.modifiers_str, True, (230, 230, 230))

                    sprite = pygame.transform.scale_by(
                        weapon.sprite_img, ((name.height + dps.height) * 1.1) / weapon.sprite_img.height
                    )

                    x_off = 15
                    y_off = 15
                    surface.blit(sprite, (x_off, y_off))
                    surface.blit(name, (x_off + sprite.width * 1.1, y_off))
                    y_off += name.height
                    surface.blit(dps, (x_off + sprite.width * 1.1, y_off))
                    surface.blit(mods, (x_off, y_off + dps.height))

            self.window.blit(surface, (0, 0))
            self.need_update = False


class MenuScreen(Screen):
    def get_back_font(self, width: int) -> pygame.font.Font:
        return get_font("PixelBit", width // 18)

    def __init__(
        self,
        window: pygame.Surface,
        clock: pygame.Clock,
        fps_cap: int = None,
        back_text: str = "Return to Main Menu",
    ):
        super().__init__(window, clock, fps_cap)

        self.orig_menu_bg = pygame.image.load(get_project_root() / "assets/main_menu.png").convert()
        self.back_button = ShadowTextButton(self.get_back_font(window.width), back_text, (176, 166, 145))

    def init_loop(self) -> None:
        super().init_loop()

        self.mouse_down = False

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.menu_bg = pygame.transform.scale_by(
            self.orig_menu_bg, max(width / self.orig_menu_bg.width, height / self.orig_menu_bg.height)
        )

        self.back_button.font = self.get_back_font(width)
        self.back_button.center = width / 2, height * 0.8
        self.back_button.update()

    def handle_event(self, event: pygame.Event, only_parent: bool = False) -> bool:
        if super().handle_event(event):
            return True

        if only_parent:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_down = True
            if self.back_button.collidepoint(*pygame.mouse.get_pos()):
                self.back_button.clicked = True
        elif self.mouse_down and event.type == pygame.MOUSEBUTTONUP:
            self.mouse_down = False
            self.back_button.clicked = False
            if self.back_button.collidepoint(*pygame.mouse.get_pos()):
                self.exit = True
                return
        elif event.type == pygame.MOUSEMOTION:
            if self.back_button.collidepoint(*pygame.mouse.get_pos()):
                self.back_button.hovered = True
                if self.mouse_down:
                    self.back_button.clicked = True
            else:
                self.back_button.hovered = False
                self.back_button.clicked = False

    def draw(self) -> None:
        self.window.blit(self.menu_bg, ((self.width - self.menu_bg.width) / 2, (self.height - self.menu_bg.height) / 2))
        self.back_button.draw(self.window)


class HardcoreWarning(MenuScreen):
    def get_warning_font(self, width: int) -> pygame.font.Font:
        return get_font("BIT", width // 14)

    def __init__(self, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(window, clock, fps_cap)

        self.warning = ShadowTextButton(
            self.get_warning_font(window.width),
            "BE WARNED, SAVE YOUR DATA BEFORE USING THIS.",
            (188, 181, 166),
            wrap_length=int(window.width * 0.8),
        )
        self.warning.font.align = pygame.FONT_CENTER

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.warning.font = self.get_warning_font(width)
        self.warning.font.align = pygame.FONT_CENTER

        self.warning.wrap_length = int(width * 0.8)
        self.warning.center = width / 2, height * 0.45
        self.warning.update()

    def draw(self) -> None:
        super().draw()

        self.warning.draw(self.window)


class Controls(MenuScreen):
    def get_control_font(self, width: int, height: int) -> pygame.font.Font:
        return get_font("PixelUnicode", min(width // 2, height) // 10)

    def __init__(self, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(window, clock, fps_cap)

        controls = [
            [
                ["A/←", "Move left"],
                ["D/→", "Move right"],
                ["W/↑/Space", "Jump"],
                ["S/↓ + W/↑/Space", "Slam"],
                ["Shift", "(Hold) Sprint (Tap) Roll"],
                ["Comma/Click", "Attack"],
            ],
            [
                ["F", "Interact"],
                ["Esc", "Pause"],
                ["B", "Back to main menu"],
                ["F11", "Toggle fullscreen"],
            ],
        ]
        self.control_font = self.get_control_font(*window.size)
        self.controls = [
            [ShadowTextButton(self.control_font, f"[{key}] {action}", (188, 181, 166)) for key, action in column]
            for column in controls
        ]

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.control_font = self.get_control_font(width, height)
        widths = [max(c.width for c in col) for col in self.controls]
        total_width = sum(widths)
        for i, column in enumerate(self.controls):
            x_off = sum(widths[:i]) if i > 0 else 0
            for j, control in enumerate(column):
                control.font = self.control_font
                control.topleft = (
                    (width - total_width) / 2 + x_off,
                    height * 0.2 + (sum(c.height * 1.2 for c in column[:j]) if j > 0 else 0),
                )
                control.update()

    def draw(self) -> None:
        super().draw()

        for col in self.controls:
            for control in col:
                control.draw(self.window)


class MainMenu(MenuScreen):
    def get_title_font(self, width: int) -> pygame.font.Font:
        return get_font("BIT", width // 10)

    def get_start_font(self, width: int) -> pygame.font.Font:
        return get_font("PixelifySans", width // 18, "Bold")

    def get_sub_font(self, width: int) -> pygame.font.Font:
        return get_font("PixelifySans", width // 24, "Bold")

    def __init__(self, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(window, clock, fps_cap, "Exit")

        self.title = ShadowTextButton(self.get_title_font(window.width), "Not so Dead Cells", (188, 181, 166))
        text_colour = 176, 166, 145
        self.start_button = ShadowTextButton(self.get_start_font(window.width), "Start Game", text_colour)
        sub_button_font = self.get_sub_font(window.width)
        self.controls_button = ShadowTextButton(sub_button_font, "Controls", text_colour)
        self.hardcore_button = Checkbox(sub_button_font, "Hardcore", text_colour, on_release=True)

        self.active_buttons = self.start_button, self.controls_button, self.hardcore_button, self.back_button
        self.needs_draw = self.title, *self.active_buttons

        self.game_screen = Game(window, clock)
        self.controls_screen = Controls(window, clock)

    def init_loop(self) -> None:
        super().init_loop()

        change_music("main_menu")
        self.hardcore_warned = False

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.title.font = self.get_title_font(width)
        self.start_button.font = self.get_start_font(width)
        sub_button_font = self.get_sub_font(width)
        self.controls_button.font = sub_button_font
        self.hardcore_button.font = sub_button_font

        self.title.center = width / 2, height * 0.3
        self.title.update()
        self.start_button.center = width / 2, height * 0.5
        self.start_button.update()
        self.controls_button.center = width / 2, height * 0.59
        self.controls_button.update()
        self.hardcore_button.center = width / 2, height * 0.66
        self.hardcore_button.update()

    def handle_event(self, event: pygame.Event) -> bool:
        if super().handle_event(event, True):
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_down = True

            for button in self.active_buttons:
                if button.collidepoint(*pygame.mouse.get_pos()):
                    button.clicked = True
        elif self.mouse_down and event.type == pygame.MOUSEBUTTONUP:
            self.mouse_down = False

            for button in self.active_buttons:
                button.clicked = False

            mouse_pos = pygame.mouse.get_pos()
            full_exit = None
            if self.start_button.collidepoint(*mouse_pos):
                full_exit = self.game_screen.main_loop()
                if not full_exit:
                    change_music("main_menu")
                    pygame.mixer.stop()
            elif self.controls_button.collidepoint(*mouse_pos):
                full_exit = self.controls_screen.main_loop()
            elif self.hardcore_button.collidepoint(*mouse_pos):
                state.hardcore = self.hardcore_button.checked
                if not self.hardcore_warned:
                    full_exit = HardcoreWarning(self.window, self.clock).main_loop()
                    self.hardcore_warned = True
            elif self.back_button.collidepoint(*pygame.mouse.get_pos()):
                full_exit = True

            if full_exit:
                return True
        elif event.type == pygame.MOUSEMOTION:
            for button in self.active_buttons:
                if button.collidepoint(*pygame.mouse.get_pos()):
                    button.hovered = True
                    if self.mouse_down:
                        button.clicked = True
                else:
                    button.hovered = False
                    is_hardcore_btn = button is self.hardcore_button
                    if is_hardcore_btn:
                        checked = button.checked
                    button.clicked = False
                    if is_hardcore_btn:
                        # Ignore when move off
                        button.checked = checked

    def draw(self) -> None:
        super().draw()

        for d in self.needs_draw:
            d.draw(self.window)
