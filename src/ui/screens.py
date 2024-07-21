from __future__ import annotations

import math
import random
from threading import Thread

import config
import pygame
import state
from camera import Camera
from map import Map
from player import Player
from util import key_handler
from util.event import (
    DIFFICULTY_CHANGED,
    PLAYER_DAMAGE_HEALTH_CHANGED,
    PLAYER_DAMAGE_MULTIPLIER_CHANGED,
    PLAYER_HEALTH_CHANGED,
    PLAYER_HEALTH_MULTIPLIER_CHANGED,
    PLAYER_MAX_HEALTH_CHANGED,
    PLAYER_MULTIPLIERS_CHANGED,
    PLAYER_WEAPON_CHANGED,
    SCORE_CHANGED,
    UI_BUTTON_PRESSED,
)
from util.func import change_music, clamp, get_font, get_fps, get_project_root
from util.type import PlayerControl, Sound

from .elements import (
    Checkbox,
    EventText,
    Grid,
    Image,
    Panel,
    ShadowText,
    ShadowTextButton,
    StackedProgressBar,
    Text,
    TextGroup,
    UIElement,
    WeaponDisplay,
)


class Screen:
    def __init__(self, parent: Screen, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        self.parent: Screen = parent
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
                if self.parent:
                    self.parent.on_resize(*self.window.size)  # Resize parent on exit
                return

            if self.update():
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
            self.on_resize(*event.size)

    def on_resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def pre_event_handling(self) -> None:
        pass

    def update(self) -> bool:
        pass

    def draw(self) -> None:
        pass


class DeathScreen(Screen):
    def __init__(self, parent: Screen, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(parent, window, clock, fps_cap)

        self.panel: Panel = Panel((0, 0), (1920, 1080), anchors={"center": "center"})
        self.death_text: Text = Text(
            (0, -100), get_font("Sabo", 172), "You Died.", container=self.panel, anchors={"center": "center"}
        )
        self.score: Text = Text(
            (0, 30),
            get_font("PixelifySans", 80),
            f"Score: {state.score}",
            container=self.panel,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.death_text},
        )
        self.prompt: Text = Text(
            (0, 150),
            get_font("Silkscreen", 60),
            "[Esc] or click anywhere to exit",
            container=self.panel,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.score},
        )

    def handle_event(self, event: pygame.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.exit = True
            return

        self.panel.handle_event(event)

    def init_loop(self) -> None:
        super().init_loop()

        change_music("game_over", "ogg")

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.panel.scale_by_ip(min(width / self.panel.width, height / self.panel.height))

    def update(self) -> None:
        self.panel.update()

    def draw(self) -> None:
        intensity = 255 * max(0, 1 - self.dt)
        self.window.fill((255, intensity, intensity), special_flags=pygame.BLEND_MULT)
        surface = pygame.transform.gaussian_blur(self.window, clamp(int(10 * self.dt), 10, 1))
        self.window.blit(surface, (0, 0))

        self.panel.draw(self.window)


class Game(Screen):
    def create_damage_tint(self, width: int, height: int, strength: int, size: int = 5) -> pygame.Surface:
        strength = 255 - strength
        surface = pygame.Surface((size, size)).convert()
        surface.fill((255, 255, 255))
        pygame.draw.rect(surface, (255, strength, strength), (0, 0, size, size), width=1)
        return pygame.transform.smoothscale(surface, (width, height))

    def create_damage_tints(self, width: int, height: int, start: int = 1, stop: int = 255, step: int = 25) -> None:
        self.damage_tints = [self.create_damage_tint(width, height, i) for i in range(start, stop, step)]
        self.max_damage_tint = len(self.damage_tints) - 1

    def __init__(self, parent: Screen, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(parent, window, clock, fps_cap)

        self.enter_map_sfx: Sound = Sound(get_project_root() / "assets/sfx/Enter_Level.wav")

        # Dummy rect for scaling
        self.dummy_rect: pygame.FRect = pygame.FRect(0, 0, 1920, 1080)

        # Overlay elements
        overlay_font = get_font("Silkscreen", 32)
        self.fps: Text = Text((15, 15), overlay_font, "FPS", (255, 255, 255))
        self.score: EventText = EventText(
            (15, 15),
            overlay_font,
            "Score: {}",
            SCORE_CHANGED,
            lambda e: e.new_value,
            state.score,
            anchors={"top": "bottom", "top_target": self.fps},
        )
        self.multipliers: EventText = EventText(
            (-15, -15),
            overlay_font,
            "Damage x{:.2f}, Health x{:.2f}",
            PLAYER_MULTIPLIERS_CHANGED,
            lambda e: (state.player.damage_mul, state.player.health_mul),
            (1, 1),
            anchors={"bottom": "bottom", "right": "right"},
        )
        self.health_bar: StackedProgressBar = StackedProgressBar(
            (15, -15),
            (400, 30),
            Player.MAX_HEALTH,
            [(213, 162, 59), (82, 191, 118)],
            2,
            progress_value=True,
            font=get_font("BIT", 14),
            border_colour=(82, 191, 118),
            border_radius=12,
            values=[0, Player.MAX_HEALTH],
            anchors={"bottom": "bottom"},
        )

        # Font for titles (pause and back screen)
        title_font = get_font("SilkscreenExpanded", 146, "Bold")

        # Pause screen
        self.pause_text: Text = Text((0, 0), title_font, "PAUSED", anchors={"center": "center"})

        # Top pause text
        self.top_pause_group: Panel = Panel(
            (0, -50), anchors={"centerx": "centerx", "bottom": "top", "bottom_target": self.pause_text}
        )
        top_pause_font = get_font("PixelifySans", 54)
        self.pause_top_sep: Text = Text(
            (0, 0), top_pause_font, "|", container=self.top_pause_group, anchors={"centerx": "centerx"}
        )
        self.pause_score: EventText = EventText(
            (-30, 0),
            top_pause_font,
            "Current score: {}",
            SCORE_CHANGED,
            lambda e: e.new_value,
            state.score,
            container=self.top_pause_group,
            anchors={"right": "left", "right_target": self.pause_top_sep},
        )
        self.pause_difficulty: EventText = EventText(
            (30, 0),
            top_pause_font,
            "Current difficulty: {:.2f}x",
            DIFFICULTY_CHANGED,
            lambda e: e.new_value,
            state.difficulty,
            container=self.top_pause_group,
            anchors={"left": "right", "left_target": self.pause_top_sep},
        )

        # Bottom pause text
        self.bottom_pause_group: Panel = Panel(
            (0, 70), anchors={"centerx": "centerx", "top": "bottom", "top_target": self.pause_text}
        )
        bottom_pause_font = get_font("PixelifySans", 46)
        self.pause_bottom_sep: Text = Text(
            (0, 0), bottom_pause_font, "|", container=self.bottom_pause_group, anchors={"centerx": "centerx"}
        )
        self.pause_damage_mul: EventText = EventText(
            (-30, 0),
            bottom_pause_font,
            "Damage multiplier: {:.2f}x",
            PLAYER_DAMAGE_MULTIPLIER_CHANGED,
            lambda e: e.new_value,
            1,
            container=self.bottom_pause_group,
            anchors={"right": "left", "right_target": self.pause_bottom_sep},
        )
        self.pause_health_mul: EventText = EventText(
            (30, 0),
            bottom_pause_font,
            "Health multiplier: {:.2f}x",
            PLAYER_HEALTH_MULTIPLIER_CHANGED,
            lambda e: e.new_value,
            1,
            container=self.bottom_pause_group,
            anchors={"left": "right", "left_target": self.pause_bottom_sep},
        )

        # Font for pause and back prompts
        prompt_font = get_font("Silkscreen", 36)

        # Pause prompts
        self.pause_prompt_group: TextGroup = TextGroup(
            (0, 140),
            prompt_font,
            ["[Esc] to resume", "[B] to return to the main menu"],
            spacing=20,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.bottom_pause_group},
        )

        # Pause weapon display
        self.weapon_display: WeaponDisplay = None

        # Back screen
        self.back_text: Text = Text((0, 0), title_font, "Really?", anchors={"center": "center"})
        self.back_prompt_group: TextGroup = TextGroup(
            (0, 200),
            prompt_font,
            ["[Esc] Nooooo, let me keep playing!", "[B] I want to leave, LET ME OUT!!!"],
            spacing=20,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.back_text},
        )

        # Loading screen text
        self.loading_text: Text = Text((0, 0), get_font("Sabo", 162), "Loading...", anchors={"center": "center"})

        # Element groups
        self.overlay_elements: tuple[UIElement, ...] = self.fps, self.score, self.multipliers, self.health_bar
        self.pause_elements: list[UIElement] = [
            self.pause_text,
            self.top_pause_group,
            self.bottom_pause_group,
            self.pause_prompt_group,
        ]
        self.back_elements: tuple[UIElement, ...] = self.back_text, self.back_prompt_group
        self.ui_elements: list[UIElement] = [
            *self.overlay_elements,
            *self.pause_elements,
            *self.back_elements,
            self.loading_text,
        ]

        # Async map loading
        self.load_map_thread: Thread | None = None

    def init_loop(self) -> None:
        state.reset()
        key_handler.reset()

        state.player = Player()
        state.camera = Camera()
        state.current_map = Map()

        state.current_map.spawn_init_weapon()

        self.health_bar.max = Player.MAX_HEALTH
        self.health_bar.values = [0, Player.MAX_HEALTH]
        self.multipliers.set_value(1, 1)
        self.pause_damage_mul.set_value(1)
        self.pause_health_mul.set_value(1)

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

        scale = min(width / self.dummy_rect.width, height / self.dummy_rect.height)
        self.dummy_rect.scale_by_ip(scale)  # Dummy rect to get scale
        for el in self.ui_elements:
            el.scale_by_ip(scale)

        self.create_damage_tints(width, height)

        self.need_update = True

    def load_map(self) -> None:
        change_music("pause")
        state.current_map.load()
        state.map_loaded = True
        self.load_map_thread = None  # Unref when done
        self.enter_map_sfx.play()
        change_music("game", "ogg", random.uniform(0, 90))

    def pre_event_handling(self) -> None:
        if not state.map_loaded and self.load_map_thread is None:
            self.load_map_thread = Thread(target=self.load_map)
            self.load_map_thread.start()

        self.moves = []
        if key_handler.get(pygame.K_LEFT) or key_handler.get(pygame.K_a):
            self.moves.append(PlayerControl.LEFT)
        if key_handler.get(pygame.K_RIGHT) or key_handler.get(pygame.K_d):
            self.moves.append(PlayerControl.RIGHT)

    def handle_event(self, event: pygame.Event) -> bool:
        if super().handle_event(event):
            return True

        for el in self.ui_elements:
            el.handle_event(event)

        if event.type == PLAYER_HEALTH_CHANGED:
            self.health_bar.set_value(event.new_value, 1)
        elif event.type == PLAYER_MAX_HEALTH_CHANGED:
            self.health_bar.max = event.new_value
        elif event.type == PLAYER_DAMAGE_HEALTH_CHANGED:
            self.health_bar.set_value(event.new_value, 0)
        elif event.type == PLAYER_WEAPON_CHANGED:
            if self.weapon_display is None:
                font = get_font("Silkscreen", 40)
                self.weapon_display = WeaponDisplay(
                    (15, 15),
                    event.new_value,
                    name_font=get_font("BIT", 48),
                    dps_font=font,
                    mods_font=font,
                    dps_colour=(180, 180, 180),
                    mods_colour=(230, 230, 230),
                )
                self.pause_elements.append(self.weapon_display)
                self.ui_elements.append(self.weapon_display)
            else:
                self.weapon_display.weapon = event.new_value
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

    def update(self) -> bool:
        self.fps.text_str = f"FPS: {round(self.clock.get_fps(), 2)}"

        for el in self.ui_elements:
            el.update()

        if state.map_loaded and not (self.paused or self.back_confirm):
            key_handler.tick(self.dt)
            state.player.tick(self.dt, self.moves)
            if state.player.top > state.current_map.height:
                state.current_map.player_out_of_bounds()
            if state.player.health <= 0:
                full_exit = DeathScreen(self, self.window, self.clock).main_loop()
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
        low_health = 0 <= state.player.health <= state.player.max_health * 0.2
        damage_flash = state.player.damage_tint_time > 0
        if low_health or damage_flash:
            intensity = 0
            if low_health:
                intensity = (1 - state.player.health / (state.player.max_health * 0.5)) * self.max_damage_tint
            if damage_flash:
                intensity = max(
                    intensity,
                    math.sin(math.pi * (state.player.damage_tint_time / state.player.damage_tint_init_time))
                    * (self.max_damage_tint / 2),
                )

            self.window.blit(self.damage_tints[int(intensity)], (0, 0), special_flags=pygame.BLEND_MULT)

    def draw(self) -> None:
        if not state.map_loaded:
            # Loading screen
            self.window.fill((0, 0, 0))
            self.loading_text.draw(self.window)
            return

        if self.need_update or not (self.paused or self.back_confirm):
            # Draw stuff
            state.camera.render(self.window)

            self.draw_damage_tint()
            for el in self.overlay_elements:
                el.draw(self.window)

        if self.need_update and (self.back_confirm or self.paused):
            # Darken and blur
            self.window.fill((140, 140, 140), special_flags=pygame.BLEND_MULT)
            surface = pygame.transform.gaussian_blur(self.window, 10)

            if self.back_confirm:
                for el in self.back_elements:
                    el.draw(surface)
            else:
                for el in self.pause_elements:
                    el.draw(surface)

            self.window.blit(surface, (0, 0))
            self.need_update = False


class MenuScreen(Screen):
    def __init__(
        self,
        parent: Screen,
        window: pygame.Surface,
        clock: pygame.Clock,
        fps_cap: int = None,
        back_text: str = "Return to Main Menu",
    ):
        super().__init__(parent, window, clock, fps_cap)

        self.background: Image = Image(
            (0, 0),
            pygame.image.load(get_project_root() / "assets/main_menu.png").convert(),
            anchors={"center": "center"},
        )

        # Panel for scaling
        self.panel: Panel = Panel((0, 0), (1920, 1080), anchors={"center": "center"})
        self.back_button = ShadowTextButton(
            (0, -140),
            get_font("PixelBit", 96),
            back_text,
            (176, 166, 145),
            container=self.panel,
            anchors={"centerx": "centerx", "bottom": "bottom"},
        )

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)

        self.background.scale_by_ip(max(width / self.background.width, height / self.background.height))
        self.panel.scale_by_ip(min(width / self.panel.width, height / self.panel.height))

    def handle_event(self, event: pygame.Event, only_parent: bool = False) -> bool:
        if super().handle_event(event):
            return True

        if event.type == UI_BUTTON_PRESSED and event.element is self.back_button:
            self.exit = True
            return

        self.background.handle_event(event)
        self.panel.handle_event(event)

    def update(self) -> None:
        self.background.update()
        self.panel.update()

    def draw(self) -> None:
        self.background.draw(self.window)
        self.panel.draw(self.window)


class HardcoreWarning(MenuScreen):
    def __init__(self, parent: Screen, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(parent, window, clock, fps_cap)

        self.warning = ShadowText(
            (0, -80),
            get_font("BIT", 108),
            "BE WARNED, SAVE YOUR DATA BEFORE USING THIS.",
            (188, 181, 166),
            wrap_length=1536,
            container=self.panel,
            anchors={"center": "center"},
        )
        self.warning.font.align = pygame.FONT_CENTER


class Controls(MenuScreen):
    def __init__(self, parent: Screen, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(parent, window, clock, fps_cap)

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
                ["Ctrl + M", "Toggle mute"],
            ],
        ]
        control_font = get_font("PixelUnicode", 70)
        self.controls = Grid(
            (0, -100),
            vertical=True,
            children=[
                [ShadowText((0, 0), control_font, f"[{key}] {action}", (188, 181, 166)) for key, action in column]
                for column in controls
            ],
            gaps=(50, 10),
            container=self.panel,
            anchors={"center": "center"},
        )


class MainMenu(MenuScreen):
    def __init__(self, window: pygame.Surface, clock: pygame.Clock, fps_cap: int = None):
        super().__init__(None, window, clock, fps_cap, "Exit")

        self.title = ShadowText(
            (0, -260),
            get_font("BIT", 200),
            "Not so Dead Cells",
            (188, 181, 166),
            container=self.panel,
            anchors={"center": "center"},
        )
        text_colour = 176, 166, 145
        self.start_button = ShadowTextButton(
            (0, 140),
            get_font("PixelifySans", 100, "Bold"),
            "Start Game",
            text_colour,
            container=self.panel,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.title},
        )
        sub_button_font = get_font("PixelifySans", 80, "Bold")
        self.controls_button = ShadowTextButton(
            (0, 40),
            sub_button_font,
            "Controls",
            text_colour,
            container=self.panel,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.start_button},
        )
        self.hardcore_button = Checkbox(
            (0, 30),
            sub_button_font,
            "Hardcore",
            text_colour,
            container=self.panel,
            anchors={"centerx": "centerx", "top": "bottom", "top_target": self.controls_button},
        )

        self.game_screen = Game(self, window, clock)
        self.controls_screen = Controls(self, window, clock)

    def init_loop(self) -> None:
        super().init_loop()

        change_music("main_menu")
        self.hardcore_warned = False

    def handle_event(self, event: pygame.Event) -> bool:
        if super().handle_event(event, True):
            return True

        if event.type == UI_BUTTON_PRESSED:
            full_exit = None
            if event.element is self.start_button:
                self.start_button.hovered = False  # No hover because moved to new screen
                full_exit = self.game_screen.main_loop()
                if not full_exit:
                    change_music("main_menu")
                    pygame.mixer.stop()
            elif event.element is self.controls_button:
                self.controls_button.hovered = False
                full_exit = self.controls_screen.main_loop()
            elif event.element is self.hardcore_button:
                state.hardcore = self.hardcore_button.checked
                if not self.hardcore_warned:
                    self.hardcore_button.hovered = False
                    # Only shows once so no point keeping a ref to it
                    full_exit = HardcoreWarning(self, self.window, self.clock).main_loop()
                    self.hardcore_warned = True

            if full_exit:
                return True
