import time

import pygame
import state
from camera import Camera
from map import Map
from player import Player
from util import key_handler
from util.func import get_font, get_project_root
from util.type import Colour, PlayerControl, Rect, Vec2


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
        self.size = self.text.size

    @property
    def hovered(self) -> bool:
        return self._hovered

    @hovered.setter
    def hovered(self, value: bool) -> None:
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

    @property
    def shadow(self) -> pygame.Surface:
        return self._shadow

    @shadow.setter
    def shadow(self, value: pygame.Surface) -> None:
        rect = value.get_bounding_rect()
        self._shadow = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
        self._shadow.blit(value, (0, 0), rect)

    def __init__(
        self, font: pygame.font.Font, text: str, colour: Colour, depth: float = 1 / 15, clicked_depth: float = 0.7
    ):
        self._font: pygame.font.Font = font
        self.text_str: str = text
        self.colour: Colour = colour
        r, g, b = colour
        self.hover_colour: Colour = r * 0.9, g * 0.9, b * 0.9
        self.shadow_colour: Colour = r * 0.1, g * 0.1, b * 0.1
        self.shadow_off: Vec2 = 1 + font.point_size * depth
        self.shadow_off_clicked: Vec2 = self.shadow_off * clicked_depth

        self._text: pygame.Surface = None
        self._shadow: pygame.Surface = None
        self._clicked: bool = False
        self._hovered: bool = False

        self.update()
        super().__init__(0, 0, self.text.width, self.text.height)

    def update(self) -> None:
        self.text = self.font.render(self.text_str, True, self.hover_colour if self.hovered else self.colour)
        self.shadow = self.font.render(self.text_str, True, self.shadow_colour)

    def draw(self, surface: pygame.Surface) -> None:
        shadow_off = self.shadow_off_clicked if self.clicked else self.shadow_off
        surface.blit(self.shadow, (self.x + shadow_off, self.y + shadow_off))
        surface.blit(self.text, self.topleft)


def LoadingScreen(window: pygame.Surface) -> None:
    window.fill((0, 0, 0))
    text = get_font("Sabo", window.width // 15).render("Loading...", True, (255, 255, 255))
    window.blit(text, ((window.width - text.width) / 2, (window.height - text.height) / 2))
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


def Game(window: pygame.Surface, clock: pygame.Clock) -> int:
    state.reset()

    state.player = Player()
    state.camera = Camera()
    state.current_map = Map()

    state.current_map.spawn_init_weapon()

    h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*window.size)

    overlay_font = None
    pause_text = None
    top_pause_font = None
    bottom_pause_font = None
    prompt_font = None
    prompts = None

    def update_fonts():
        nonlocal overlay_font, pause_text, top_pause_font, bottom_pause_font, prompt_font, prompts
        overlay_font = get_font("Silkscreen", window.width // 60)
        pause_text = get_font("SilkscreenExpanded", window.width // 10, "Bold").render("PAUSED", True, (255, 255, 255))
        top_pause_font = get_font("PixelifySans", window.width // 30)
        bottom_pause_font = get_font("PixelifySans", window.width // 40)
        prompt_font = get_font("Silkscreen", window.width // 45)
        prompts = [
            prompt_font.render("[Esc] to resume", True, (255, 255, 255)),
            prompt_font.render("[B] to return to the main menu", True, (255, 255, 255)),
        ]

    update_fonts()

    pause = False
    skip_frame = False
    do_blur = True

    while True:
        # FPS = refresh rate or default 60
        dt = clock.tick(pygame.display.get_current_refresh_rate() or 60) / 1000  # To get in seconds

        # Do not count loading time
        if not state.map_loaded:
            LoadingScreen(window)
            state.current_map.load()
            state.map_loaded = True
            skip_frame = True
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
                pygame.quit()
                return True
            elif event.type == pygame.VIDEORESIZE:
                new_size = event.dict["size"]
                state.camera.resize(*new_size)
                if not state.current_map.static_bg:
                    state.current_map.background.resize(*new_size)
                h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*new_size)
                update_fonts()
            elif event.type == pygame.KEYDOWN:
                # TODO changeable keybinds
                key_handler.down(event.key)
                if key_handler.get_control(PlayerControl.SLAM):
                    move_types.append(PlayerControl.SLAM)
                elif key_handler.get_control(PlayerControl.JUMP):
                    move_types.append(PlayerControl.JUMP)
                elif event.key == pygame.K_f:
                    move_types.append(PlayerControl.INTERACT)
                elif event.key == pygame.K_COMMA:
                    move_types.append(PlayerControl.ATTACK_START)
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    state.player.sprinting = True
                elif event.key == pygame.K_ESCAPE:
                    pause = not pause
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

        if not pause:
            key_handler.tick(dt)
            state.player.tick(dt, move_types)
            if state.player.health <= 0:
                return
            state.current_map.tick(dt)
            cam_movement = state.camera.tick_move(dt)
            if not state.current_map.static_bg:
                state.current_map.background.tick(*cam_movement)

        # Draw stuff
        state.camera.render(window)

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

        if pause:
            surface = pygame.Surface(window.size)
            surface.fill((0, 0, 0))
            surface.set_alpha(100)
            window.blit(surface, (0, 0))
            # Don't do blur if blur too slow
            if do_blur:
                start = time.process_time()
                surface = pygame.transform.gaussian_blur(window, 10)
                if time.process_time() - start > 0.3:
                    do_blur = False
            else:
                surface = window

            # Centered pause text
            y_off = (window.height - pause_text.height) / 2
            surface.blit(pause_text, ((window.width - pause_text.width) / 2, y_off))

            # Score and difficulty
            score = top_pause_font.render(f"Current score: {state.score}  ", True, (255, 255, 255))
            surface.blit(score, (window.width / 2 - score.width - 10, y_off * 0.8 - score.height / 2))
            separator = top_pause_font.render("|", True, (255, 255, 255))
            surface.blit(separator, (window.width / 2 - separator.width, y_off * 0.8 - separator.height / 2))
            difficulty = top_pause_font.render(f" Current difficulty: {state.difficulty}x", True, (255, 255, 255))
            surface.blit(difficulty, (window.width / 2 + 10, y_off * 0.8 - difficulty.height / 2))

            # Multipliers
            damage = bottom_pause_font.render(
                f"Damage multiplier: {round(state.player.damage_mul, 2)}x  ", True, (255, 255, 255)
            )
            surface.blit(
                damage, (window.width / 2 - damage.width - 10, (y_off + pause_text.height) * 1.1 - damage.height / 2)
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

            height = sum([p.height for p in prompts])
            for i, prompt in enumerate(prompts):
                surface.blit(
                    prompt,
                    (
                        (window.width - prompt.width) / 2,
                        (y_off + pause_text.height) * 1.3 - height / 2 + (prompts[i - 1].height if i > 0 else 0),
                    ),
                )

            if state.player.weapon:
                weapon = state.player.weapon
                font = pygame.font.SysFont("Rubik", window.width // 60)
                name = pygame.font.SysFont("Gabarito", window.width // 50, bold=True).render(
                    weapon.name, True, (255, 255, 255)
                )
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

        # Update window
        pygame.display.update()


def Controls(window: pygame.Surface, clock: pygame.Clock) -> int:
    orig_menu_bg = pygame.image.load(get_project_root() / "assets/main_menu.jpg").convert()
    menu_bg = None

    back_button = ShadowTextButton(get_font("PixelBit", window.width // 18), "Return to Main Menu", (176, 166, 145))

    def update_menu_bg():
        nonlocal menu_bg
        if window.width > window.height:
            menu_bg = pygame.transform.scale_by(orig_menu_bg, window.width / orig_menu_bg.width)
        else:
            menu_bg = pygame.transform.scale_by(orig_menu_bg, window.height / orig_menu_bg.height)

    def update_text_positions():
        back_button.center = window.width / 2, window.height * 0.8
        back_button.update()

    update_menu_bg()
    update_text_positions()

    mouse_down = False

    while True:
        # Limit fps
        clock.tick(pygame.display.get_current_refresh_rate() or 60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
                if back_button.collidepoint(*pygame.mouse.get_pos()):
                    back_button.clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
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

                back_button.font = get_font("PixelBit", window.width // 18)
                update_text_positions()

        window.blit(menu_bg, ((window.width - menu_bg.width) / 2, (window.height - menu_bg.height) / 2))
        back_button.draw(window)

        # Update window
        pygame.display.update()


def MainMenu(window: pygame.Surface, clock: pygame.Clock) -> None:
    orig_menu_bg = pygame.image.load(get_project_root() / "assets/main_menu.jpg").convert()
    menu_bg = None

    title = ShadowTextButton(get_font("BIT", window.width // 10), "Not so Dead Cells", (188, 181, 166))
    start_button = ShadowTextButton(get_font("PixelifySans", window.width // 18, "Bold"), "Start Game", (176, 166, 145))
    controls_button = ShadowTextButton(
        get_font("PixelifySans", window.width // 20, "Bold"), "Controls", (176, 166, 145)
    )
    exit_button = ShadowTextButton(get_font("PixelBit", window.width // 18), "Exit", (176, 166, 145))

    active_buttons = start_button, controls_button, exit_button
    draw = title, *active_buttons

    def update_menu_bg():
        nonlocal menu_bg
        if window.width > window.height:
            menu_bg = pygame.transform.scale_by(orig_menu_bg, window.width / orig_menu_bg.width)
        else:
            menu_bg = pygame.transform.scale_by(orig_menu_bg, window.height / orig_menu_bg.height)

    def update_text_positions():
        title.center = window.width / 2, window.height * 0.3
        title.update()
        start_button.center = window.width / 2, window.height * 0.5
        start_button.update()
        controls_button.center = window.width / 2, window.height * 0.6
        controls_button.update()
        exit_button.center = window.width / 2, window.height * 0.8
        exit_button.update()

    update_menu_bg()
    update_text_positions()

    mouse_down = False

    while True:
        # Limit fps
        clock.tick(pygame.display.get_current_refresh_rate() or 60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_down = True
                for button in active_buttons:
                    if button.collidepoint(*pygame.mouse.get_pos()):
                        button.clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_down = False

                start_button.clicked = False
                controls_button.clicked = False
                exit_button.clicked = False

                full_exit = None
                if start_button.collidepoint(*pygame.mouse.get_pos()):
                    full_exit = Game(window, clock)
                elif controls_button.collidepoint(*pygame.mouse.get_pos()):
                    full_exit = Controls(window, clock)
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
                controls_button.font = get_font("PixelifySans", window.width // 20, "Bold")
                exit_button.font = get_font("PixelBit", window.width // 18)
                update_text_positions()

        window.blit(menu_bg, ((window.width - menu_bg.width) / 2, (window.height - menu_bg.height) / 2))
        for d in draw:
            d.draw(window)

        # Update window
        pygame.display.update()
