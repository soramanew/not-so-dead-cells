import pygame
import state
from camera import Camera
from map import Map
from player import Player
from util import key_handler
from util.type import Colour, PlayerControl, Rect

H_BAR_COLOUR: Colour = 82, 191, 118


def _h_bar_rect(width: int, height: int) -> Rect:
    h_bar_height = height * 0.04
    return 50, height - h_bar_height - 50, width * 0.33, h_bar_height


def _h_bar_inner_rect(width: int, height: int) -> Rect:
    i_w = 0.97  # inner width
    i_h = 0.7  # inner height
    x, y, w, h = _h_bar_rect(width, height)
    return x + w * (1 - i_w) / 2, y + h * (1 - i_h) / 2, w * i_w, h * i_h


def _create_h_bar(width: int, height: int) -> tuple[pygame.Surface, Rect, pygame.font.SysFont]:
    h_bar = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    pygame.draw.rect(h_bar, (0, 0, 0, 100), _h_bar_rect(width, height), border_radius=3)
    inner_rect = _h_bar_inner_rect(width, height)
    pygame.draw.rect(h_bar, H_BAR_COLOUR, inner_rect, width=1, border_radius=10)
    return h_bar, inner_rect, pygame.font.SysFont("Rubik", int(height * 0.02))


def main():
    pygame.init()

    window = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    state.player = Player()
    state.current_map = Map()
    state.camera = Camera()

    state.current_map.spawn_init_weapon()

    font_rubik = pygame.font.SysFont("Rubik", 20)

    h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*window.size)

    pause = False
    skip_frame = False

    while True:
        # FPS = refresh rate or default 60
        dt = clock.tick(pygame.display.get_current_refresh_rate() or 60) / 1000  # To get in seconds

        # Do not count loading time
        if not state.map_loaded:
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
                return
            elif event.type == pygame.VIDEORESIZE:
                new_size = event.dict["size"]
                state.camera.resize(*new_size)
                if not state.current_map.static_bg:
                    state.current_map.background.resize(*new_size)
                h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*new_size)
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
                time = key_handler.up(event.key)
                if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if time < key_handler.TAP_THRESHOLD:
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
            state.current_map.tick(dt)
            cam_movement = state.camera.tick_move(dt)
            if not state.current_map.static_bg:
                state.current_map.background.tick(*cam_movement)

        # Draw stuff
        state.camera.render(window)

        # FPS monitor
        fps = font_rubik.render(f"FPS: {round(clock.get_fps(), 2)}", True, (255, 255, 255))
        window.blit(fps, (15, 15))

        # Score
        window.blit(font_rubik.render(f"Score: {state.score}", True, (255, 255, 255)), (15, 15 + fps.height))

        multipliers = font_rubik.render(
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
            H_BAR_COLOUR,
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
        player_health = h_bar_font.render(f"{state.player.health} / {state.player.max_health}", True, (255, 255, 255))
        window.blit(
            player_health,
            (
                h_bar_inner_rect[0] + h_bar_inner_rect[2] / 2 - player_health.width / 2,
                h_bar_inner_rect[1] + h_bar_inner_rect[3] / 2 - player_health.height / 2,
            ),
        )

        if pause:
            surface = pygame.Surface(window.size)
            surface.fill((0, 0, 0))
            surface.set_alpha(100)
            window.blit(surface, (0, 0))
            surface = pygame.transform.gaussian_blur(window, 10)

            # Centered pause text
            pause_text = pygame.font.SysFont("Gabarito", window.width // 15, bold=True).render(
                "PAUSED", True, (255, 255, 255)
            )
            y_off = (window.height - pause_text.height) / 2
            surface.blit(pause_text, ((window.width - pause_text.width) / 2, y_off))

            # Score and difficulty
            font = pygame.font.SysFont("Rubik", window.width // 30)
            score = font.render(f"Current score: {state.score}  ", True, (255, 255, 255))
            surface.blit(score, (window.width / 2 - score.width - 10, y_off * 0.8 - score.height / 2))
            separator = font.render("|", True, (255, 255, 255))
            surface.blit(separator, (window.width / 2 - separator.width, y_off * 0.8 - separator.height / 2))
            difficulty = font.render(f" Current difficulty: {state.difficulty}x", True, (255, 255, 255))
            surface.blit(difficulty, (window.width / 2 + 10, y_off * 0.8 - difficulty.height / 2))

            # Multipliers
            font = pygame.font.SysFont("Rubik", window.width // 40)
            damage = font.render(f"Damage multiplier: {state.player.damage_mul}x  ", True, (255, 255, 255))
            surface.blit(
                damage, (window.width / 2 - damage.width - 10, (y_off + pause_text.height) * 1.2 - damage.height / 2)
            )
            separator = font.render("|", True, (255, 255, 255))
            surface.blit(
                separator,
                (window.width / 2 - separator.width, (y_off + pause_text.height) * 1.2 - separator.height / 2),
            )
            health = font.render(f" Health multiplier: {state.player.health_mul}x", True, (255, 255, 255))
            surface.blit(health, (window.width / 2 + 10, (y_off + pause_text.height) * 1.2 - health.height / 2))

            prompt = pygame.font.SysFont("Readex Pro", window.width // 45).render(
                "[Esc] to resume", True, (255, 255, 255)
            )
            surface.blit(
                prompt, ((window.width - prompt.width) / 2, (y_off + pause_text.height) * 1.35 - prompt.height / 2)
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


if __name__ == "__main__":
    main()
