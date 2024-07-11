import math
import random

import pygame
import state
from camera import Camera
from map import Map
from player import Player
from util import key_handler
from util.func import change_music, clamp, get_font, get_fps, get_project_root
from util.type import Colour, PlayerControl, Rect, Side, Sound, Vec2


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


def LoadingScreen(window: pygame.Surface) -> None:
    window.fill((0, 0, 0))
    text = get_font("Sabo", window.width // 15).render("Loading...", True, (255, 255, 255))
    window.blit(text, ((window.width - text.width) / 2, (window.height - text.height) / 2))
    pygame.display.update()


def DeathScreen(window: pygame.Surface, clock: pygame.Clock) -> bool:
    change_music("game_over", "ogg")

    death_text = None
    score = None
    prompt = None

    def update_text() -> None:
        nonlocal death_text, score, prompt
        death_text = get_font("Sabo", window.width // 15).render("You Died.", True, (255, 255, 255))
        death_text = death_text, ((window.width - death_text.width) / 2, (window.height - death_text.height) / 2)

        score = get_font("PixelifySans", window.width // 45).render(f"Score: {state.score}", True, (255, 255, 255))
        score = score, ((window.width - score.width) / 2, window.height * 0.6 - score.height / 2)

        prompt = get_font("Silkscreen", window.width // 45).render("Click anywhere to exit", True, (255, 255, 255))
        prompt = prompt, ((window.width - prompt.width) / 2, window.height * 0.8 - prompt.height / 2)

    update_text()

    while True:
        dt = clock.tick(30) / 1000  # To get in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                return
            elif event.type == pygame.VIDEORESIZE:
                update_text()

        intensity = 255 * max(0, 1 - dt)
        window.fill((255, intensity, intensity), special_flags=pygame.BLEND_MULT)
        surface = pygame.transform.gaussian_blur(window, clamp(int(10 * dt), 10, 1))
        window.blit(surface, (0, 0))

        window.blit(*death_text)
        window.blit(*score)
        window.blit(*prompt)

        pygame.display.update()


def _h_bar_rect(width: int, height: int) -> Rect:
    h_bar_height = height * 0.04
    return 50, height - h_bar_height - 50, width * 0.33, h_bar_height


def _h_bar_inner_rect(width: int, height: int) -> Rect:
    i_w = 0.97  # inner width
    i_h = 0.7  # inner height
    x, y, w, h = _h_bar_rect(width, height)
    return x + w * (1 - i_w) / 2, y + h * (1 - i_h) / 2, w * i_w, h * i_h


def _create_h_bar(width: int, height: int) -> tuple[pygame.Surface, Rect, pygame.font.Font]:
    h_bar = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    pygame.draw.rect(h_bar, (0, 0, 0, 100), _h_bar_rect(width, height), border_radius=3)
    inner_rect = _h_bar_inner_rect(width, height)
    pygame.draw.rect(h_bar, (82, 191, 118), inner_rect, width=1, border_radius=10)
    return h_bar, inner_rect, get_font("BIT", int(height * 0.02))


def _create_damage_tint(width: int, height: int, strength: int, size: int = 5) -> pygame.Surface:
    strength = 255 - strength
    surface = pygame.Surface((size, size)).convert()
    surface.fill((255, 255, 255))
    pygame.draw.rect(surface, (255, strength, strength), (0, 0, size, size), width=1)
    return pygame.transform.smoothscale(surface, (width, height))


def _create_damage_tints(
    width: int, height: int, start: int = 1, stop: int = 255, step: int = 25
) -> tuple[list[pygame.Surface], int]:
    tints = [_create_damage_tint(width, height, i) for i in range(start, stop, step)]
    return tints, len(tints) - 1


def Game(window: pygame.Surface, clock: pygame.Clock) -> int:
    state.reset()
    key_handler.reset()

    state.player = Player()
    state.camera = Camera()
    state.current_map = Map()

    state.current_map.spawn_init_weapon()

    h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*window.size)
    damage_tints, max_damage_tint = _create_damage_tints(*window.size)

    overlay_font = None
    title_font = None
    top_pause_font = None
    bottom_pause_font = None
    prompt_font = None
    pause_prompts = None
    back_prompts = None

    def update_fonts():
        nonlocal overlay_font, title_font, top_pause_font, bottom_pause_font, prompt_font, pause_prompts, back_prompts
        overlay_font = get_font("Silkscreen", window.width // 60)
        title_font = get_font("SilkscreenExpanded", window.width // 10, "Bold")
        top_pause_font = get_font("PixelifySans", window.width // 30)
        bottom_pause_font = get_font("PixelifySans", window.width // 40)
        prompt_font = get_font("Silkscreen", window.width // 45)
        pause_prompts = [
            prompt_font.render("[Esc] to resume", True, (255, 255, 255)),
            prompt_font.render("[B] to return to the main menu", True, (255, 255, 255)),
        ]
        back_prompts = [
            prompt_font.render("[Esc] Nooooo, let me keep playing!", True, (255, 255, 255)),
            prompt_font.render("[B] I want to leave, LET ME OUT!!!", True, (255, 255, 255)),
        ]

    update_fonts()

    pause = False
    skip_frame = False
    back_confirm = False
    menu_needs_update = False

    enter_map_sfx = Sound(get_project_root() / "assets/sfx/Enter_Level.wav")

    while True:
        # FPS = refresh rate or default 60
        dt = clock.tick(get_fps()) / 1000  # To get in seconds

        # Do not count loading time
        if not state.map_loaded:
            change_music("pause")
            LoadingScreen(window)
            state.current_map.load()
            state.map_loaded = True
            skip_frame = True
            enter_map_sfx.play()
            change_music("game", "ogg", random.uniform(0, 90))
            continue

        if skip_frame:
            skip_frame = False
            continue

        move_types = []

        if key_handler.get(pygame.K_LEFT) or key_handler.get(pygame.K_a):
            move_types.append(PlayerControl.LEFT)
        if key_handler.get(pygame.K_RIGHT) or key_handler.get(pygame.K_d):
            move_types.append(PlayerControl.RIGHT)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.VIDEORESIZE:
                new_size = event.dict["size"]
                state.camera.resize(*new_size)
                if not state.current_map.static_bg:
                    state.current_map.background.resize(*new_size)
                h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*new_size)
                damage_tints, max_damage_tint = _create_damage_tints(*new_size)
                update_fonts()
                menu_needs_update = True
            elif event.type == pygame.KEYDOWN:
                # TODO changeable keybinds
                key_handler.down(event.key)
                jump = event.key == pygame.K_w or event.key == pygame.K_UP or event.key == pygame.K_SPACE
                if (key_handler.get(pygame.K_s) or key_handler.get(pygame.K_DOWN)) and jump:
                    move_types.append(PlayerControl.SLAM)
                elif jump:
                    move_types.append(PlayerControl.JUMP)
                elif event.key == pygame.K_f:
                    move_types.append(PlayerControl.INTERACT)
                elif event.key == pygame.K_COMMA:
                    move_types.append(PlayerControl.ATTACK_START)
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    state.player.sprinting = True
                elif event.key == pygame.K_ESCAPE:
                    if back_confirm:
                        back_confirm = False
                    else:
                        pause = not pause
                    if pause:
                        change_music("pause")
                        pygame.mixer.pause()
                    else:
                        change_music("game", "ogg", random.uniform(0, 90))
                        pygame.mixer.unpause()
                    menu_needs_update = True
                elif event.key == pygame.K_b:
                    if back_confirm:
                        return
                    change_music("pause")
                    pygame.mixer.pause()
                    back_confirm = True
                    menu_needs_update = True
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
            elif event.type == pygame.KEYUP:
                held_time = key_handler.up(event.key)
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if held_time < key_handler.TAP_THRESHOLD:
                        move_types.append(PlayerControl.ROLL)
                    state.player.sprinting = False
                elif event.key == pygame.K_COMMA:
                    move_types.append(PlayerControl.ATTACK_STOP)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                move_types.append(PlayerControl.ATTACK_START)
            elif event.type == pygame.MOUSEBUTTONUP:
                move_types.append(PlayerControl.ATTACK_STOP)

        if menu_needs_update or not (pause or back_confirm):
            if not (pause or back_confirm):
                key_handler.tick(dt)
                state.player.tick(dt, move_types)
                if state.player.health <= 0:
                    full_exit = DeathScreen(window, clock)
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
                    return full_exit
                state.current_map.tick(dt)
                cam_movement = state.camera.tick_move(dt)
                if not state.current_map.static_bg:
                    state.current_map.background.tick(*cam_movement)

            # Draw stuff
            state.camera.render(window)

            if 0 <= state.player.health <= state.player.max_health * 0.2:
                # Low health tint
                window.blit(
                    damage_tints[int((1 - state.player.health / (state.player.max_health * 0.5)) * max_damage_tint)],
                    (0, 0),
                    special_flags=pygame.BLEND_MULT,
                )
            elif state.player.damage_tint_time > 0:
                # Damage flash
                window.blit(
                    damage_tints[
                        int(
                            math.sin(math.pi * (state.player.damage_tint_time / state.player.damage_tint_init_time))
                            * (max_damage_tint / 2)
                        )
                    ],
                    (0, 0),
                    special_flags=pygame.BLEND_MULT,
                )

            # FPS monitor
            fps = overlay_font.render(f"FPS: {round(clock.get_fps(), 2)}", True, (255, 255, 255))
            window.blit(fps, (15, 15))

            # Score
            window.blit(overlay_font.render(f"Score: {state.score}", True, (255, 255, 255)), (15, 15 + fps.height))

            multipliers = overlay_font.render(
                f"Damage x{round(state.player.damage_mul, 2)}, Health x{round(state.player.health_mul, 2)}",
                True,
                (255, 255, 255),
            )
            window.blit(multipliers, (window.width - 15 - multipliers.width, window.height - 15 - multipliers.height))

            # Draw GUI
            window.blit(h_bar, (0, 0))  # Health bar base
            # Health bar health gain opportunity
            border = 0 if state.player.health < state.player.max_health else -1
            if state.player.damage_health >= 1:
                pygame.draw.rect(
                    window,
                    (213, 162, 59),
                    (
                        h_bar_inner_rect[0],
                        h_bar_inner_rect[1],
                        h_bar_inner_rect[2]
                        * ((state.player.health + state.player.damage_health) / state.player.max_health),
                        h_bar_inner_rect[3],
                    ),
                    border_radius=10,
                    border_top_right_radius=border,
                    border_bottom_right_radius=border,
                )
            # Actual health
            border = 0 if state.player.health + state.player.damage_health < state.player.max_health else -1
            pygame.draw.rect(
                window,
                (82, 191, 118),
                (
                    h_bar_inner_rect[0],
                    h_bar_inner_rect[1],
                    h_bar_inner_rect[2] * (state.player.health / state.player.max_health),
                    h_bar_inner_rect[3],
                ),
                border_radius=10,
                border_top_right_radius=border,
                border_bottom_right_radius=border,
            )
            # Health text
            health_text_uncropped = h_bar_font.render(
                f"{state.player.health} / {state.player.max_health}", True, (255, 255, 255)
            )
            health_text_rect = health_text_uncropped.get_bounding_rect()
            player_health = pygame.Surface(health_text_rect.size, pygame.SRCALPHA)
            player_health.blit(health_text_uncropped, (0, 0), health_text_rect)
            window.blit(
                player_health,
                (
                    h_bar_inner_rect[0] + (h_bar_inner_rect[2] - player_health.width) / 2,
                    h_bar_inner_rect[1] + (h_bar_inner_rect[3] - player_health.height) / 2,
                ),
            )

        if menu_needs_update and (back_confirm or pause):
            # Darken and blur
            window.fill((140, 140, 140), special_flags=pygame.BLEND_MULT)
            surface = pygame.transform.gaussian_blur(window, 10)

            if back_confirm:
                # Question
                confirm = title_font.render("Really?", True, (255, 255, 255))
                y_off = (surface.height - confirm.height) / 2
                surface.blit(confirm, ((surface.width - confirm.width) / 2, y_off))

                # Prompts
                height = sum([p.height for p in back_prompts])
                for i, prompt in enumerate(back_prompts):
                    surface.blit(
                        prompt,
                        (
                            (surface.width - prompt.width) / 2,
                            (y_off + confirm.height) * 1.3
                            - height / 2
                            + (sum(p.height for p in back_prompts[:i]) if i > 0 else 0),
                        ),
                    )
            else:
                # Centered pause text
                pause_text = title_font.render("PAUSED", True, (255, 255, 255))
                y_off = (window.height - pause_text.height) / 2
                surface.blit(pause_text, ((window.width - pause_text.width) / 2, y_off))

                # Score and difficulty
                score = top_pause_font.render(f"Current score: {state.score}  ", True, (255, 255, 255))
                surface.blit(score, (window.width / 2 - score.width - 10, y_off * 0.8 - score.height / 2))
                separator = top_pause_font.render("|", True, (255, 255, 255))
                surface.blit(separator, (window.width / 2 - separator.width, y_off * 0.8 - separator.height / 2))
                difficulty = top_pause_font.render(
                    f" Current difficulty: {round(state.difficulty, 2)}x", True, (255, 255, 255)
                )
                surface.blit(difficulty, (window.width / 2 + 10, y_off * 0.8 - difficulty.height / 2))

                # Multipliers
                damage = bottom_pause_font.render(
                    f"Damage multiplier: {round(state.player.damage_mul, 2)}x  ", True, (255, 255, 255)
                )
                surface.blit(
                    damage,
                    (window.width / 2 - damage.width - 10, (y_off + pause_text.height) * 1.1 - damage.height / 2),
                )
                separator = bottom_pause_font.render("|", True, (255, 255, 255))
                surface.blit(
                    separator,
                    (window.width / 2 - separator.width, (y_off + pause_text.height) * 1.1 - separator.height / 2),
                )
                health = bottom_pause_font.render(
                    f" Health multiplier: {round(state.player.health_mul, 2)}x", True, (255, 255, 255)
                )
                surface.blit(health, (window.width / 2 + 10, (y_off + pause_text.height) * 1.1 - health.height / 2))

                height = sum([p.height for p in pause_prompts])
                for i, prompt in enumerate(pause_prompts):
                    surface.blit(
                        prompt,
                        (
                            (window.width - prompt.width) / 2,
                            (y_off + pause_text.height) * 1.3
                            - height / 2
                            + (sum(p.height for p in pause_prompts[:i]) if i > 0 else 0),
                        ),
                    )

                if state.player.weapon:
                    weapon = state.player.weapon
                    font = get_font("Silkscreen", window.width // 60)
                    name = get_font("BIT", window.width // 50).render(weapon.name, True, (255, 255, 255))
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

            window.blit(surface, (0, 0))
            menu_needs_update = False

        # Update window
        pygame.display.update()


def _get_menu_bg():
    return pygame.image.load(get_project_root() / "assets/main_menu.png").convert()


def HardcoreWarning(window: pygame.Surface, clock: pygame.Clock) -> bool:
    orig_menu_bg = _get_menu_bg()
    menu_bg = None

    warning = ShadowTextButton(
        get_font("BIT", window.width // 14),
        "BE WARNED, SAVE YOUR DATA BEFORE USING THIS.",
        (188, 181, 166),
        wrap_length=int(window.width * 0.8),
    )
    warning.font.align = pygame.FONT_CENTER
    back_button = ShadowTextButton(get_font("PixelBit", window.width // 18), "Return to Main Menu", (176, 166, 145))

    def update_menu_bg():
        nonlocal menu_bg
        menu_bg = pygame.transform.scale_by(
            orig_menu_bg, max(window.width / orig_menu_bg.width, window.height / orig_menu_bg.height)
        )

    def update_text_positions():
        warning.wrap_length = int(window.width * 0.8)
        warning.center = window.width / 2, window.height * 0.45
        warning.update()
        back_button.center = window.width / 2, window.height * 0.8
        back_button.update()

    update_menu_bg()
    update_text_positions()

    mouse_down = False

    while True:
        # Limit fps
        clock.tick(get_fps())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    back_button.clicked = True
            elif mouse_down and event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False
                back_button.clicked = False
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    return
            elif event.type == pygame.MOUSEMOTION:
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    back_button.hovered = True
                    if mouse_down:
                        back_button.clicked = True
                else:
                    back_button.hovered = False
                    back_button.clicked = False
            elif event.type == pygame.VIDEORESIZE:
                update_menu_bg()

                warning.font = get_font("BIT", window.width // 14)
                warning.font.align = pygame.FONT_CENTER
                back_button.font = get_font("PixelBit", window.width // 18)
                update_text_positions()

        window.blit(menu_bg, ((window.width - menu_bg.width) / 2, (window.height - menu_bg.height) / 2))
        warning.draw(window)
        back_button.draw(window)

        # Update window
        pygame.display.update()


def Controls(window: pygame.Surface, clock: pygame.Clock) -> int:
    orig_menu_bg = _get_menu_bg()
    menu_bg = None

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
    control_font = get_font("PixelUnicode", min(window.width // 2, window.height) // 10)
    controls = [
        [ShadowTextButton(control_font, f"[{key}] {action}", (188, 181, 166)) for key, action in column]
        for column in controls
    ]

    back_button = ShadowTextButton(get_font("PixelBit", window.width // 18), "Return to Main Menu", (176, 166, 145))

    def update_menu_bg():
        nonlocal menu_bg
        menu_bg = pygame.transform.scale_by(
            orig_menu_bg, max(window.width / orig_menu_bg.width, window.height / orig_menu_bg.height)
        )

    def update_text_positions():
        widths = [max(c.width for c in col) for col in controls]
        total_width = sum(widths)
        for i, column in enumerate(controls):
            x_off = sum(widths[:i]) if i > 0 else 0
            for j, control in enumerate(column):
                control.font = control_font
                control.topleft = (
                    (window.width - total_width) / 2 + x_off,
                    window.height * 0.2 + (sum(c.height * 1.2 for c in column[:j]) if j > 0 else 0),
                )
                control.update()
        back_button.center = window.width / 2, window.height * 0.8
        back_button.update()

    update_menu_bg()
    update_text_positions()

    mouse_down = False

    while True:
        # Limit fps
        clock.tick(get_fps())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    back_button.clicked = True
            elif mouse_down and event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False
                back_button.clicked = False
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    return
            elif event.type == pygame.MOUSEMOTION:
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    back_button.hovered = True
                    if mouse_down:
                        back_button.clicked = True
                else:
                    back_button.hovered = False
                    back_button.clicked = False
            elif event.type == pygame.VIDEORESIZE:
                update_menu_bg()

                control_font = get_font("PixelUnicode", min(window.width // 2, window.height) // 10)
                back_button.font = get_font("PixelBit", window.width // 18)
                update_text_positions()

        window.blit(menu_bg, ((window.width - menu_bg.width) / 2, (window.height - menu_bg.height) / 2))
        for col in controls:
            for control in col:
                control.draw(window)
        back_button.draw(window)

        # Update window
        pygame.display.update()


def MainMenu(window: pygame.Surface, clock: pygame.Clock) -> None:
    change_music("main_menu")

    orig_menu_bg = _get_menu_bg()
    menu_bg = None

    title = ShadowTextButton(get_font("BIT", window.width // 10), "Not so Dead Cells", (188, 181, 166))
    text_colour = 176, 166, 145
    start_button = ShadowTextButton(get_font("PixelifySans", window.width // 18, "Bold"), "Start Game", text_colour)
    sub_button_font = get_font("PixelifySans", window.width // 24, "Bold")
    controls_button = ShadowTextButton(sub_button_font, "Controls", text_colour)
    hardcore_button = Checkbox(sub_button_font, "Hardcore", text_colour, on_release=True)
    exit_button = ShadowTextButton(get_font("PixelBit", window.width // 18), "Exit", text_colour)

    active_buttons = start_button, controls_button, hardcore_button, exit_button
    draw = title, *active_buttons

    def update_menu_bg():
        nonlocal menu_bg
        menu_bg = pygame.transform.scale_by(
            orig_menu_bg, max(window.width / orig_menu_bg.width, window.height / orig_menu_bg.height)
        )

    def update_text_positions():
        title.center = window.width / 2, window.height * 0.3
        title.update()
        start_button.center = window.width / 2, window.height * 0.5
        start_button.update()
        controls_button.center = window.width / 2, window.height * 0.59
        controls_button.update()
        hardcore_button.center = window.width / 2, window.height * 0.66
        hardcore_button.update()
        exit_button.center = window.width / 2, window.height * 0.8
        exit_button.update()

    update_menu_bg()
    update_text_positions()

    mouse_down = False
    hardcore_warned = False

    while True:
        # Limit fps
        clock.tick(get_fps())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
                for button in active_buttons:
                    if button.collidepoint(*pygame.mouse.get_pos()):
                        button.clicked = True
            elif mouse_down and event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False

                for button in active_buttons:
                    button.clicked = False

                full_exit = None
                if start_button.collidepoint(*pygame.mouse.get_pos()):
                    full_exit = Game(window, clock)
                    if not full_exit:
                        change_music("main_menu")
                        pygame.mixer.stop()
                elif controls_button.collidepoint(*pygame.mouse.get_pos()):
                    full_exit = Controls(window, clock)
                elif hardcore_button.collidepoint(*pygame.mouse.get_pos()):
                    state.hardcore = hardcore_button.checked
                    if not hardcore_warned:
                        full_exit = HardcoreWarning(window, clock)
                        hardcore_warned = True
                elif exit_button.collidepoint(*pygame.mouse.get_pos()):
                    full_exit = True

                if full_exit:
                    return
            elif event.type == pygame.MOUSEMOTION:
                for button in active_buttons:
                    if button.collidepoint(*pygame.mouse.get_pos()):
                        button.hovered = True
                        if mouse_down:
                            button.clicked = True
                    else:
                        button.hovered = False
                        button.clicked = False
            elif event.type == pygame.VIDEORESIZE:
                update_menu_bg()

                title.font = get_font("BIT", window.width // 10)
                start_button.font = get_font("PixelifySans", window.width // 18, "Bold")
                sub_button_font = get_font("PixelifySans", window.width // 24, "Bold")
                controls_button.font = sub_button_font
                hardcore_button.font = sub_button_font
                exit_button.font = get_font("PixelBit", window.width // 18)
                update_text_positions()

        window.blit(menu_bg, ((window.width - menu_bg.width) / 2, (window.height - menu_bg.height) / 2))
        for d in draw:
            d.draw(window)

        # Update window
        pygame.display.update()
