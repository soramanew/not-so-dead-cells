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
    state.current_map = Map("prisoners_quarters")
    state.current_map.spawn_enemies()
    camera = Camera()

    font_rubik = pygame.font.SysFont("Rubik", 20)

    h_bar, h_bar_inner_rect, h_bar_font = _create_h_bar(*window.size)

    pause = False

    while True:
        # FPS = refresh rate or default 60
        dt = clock.tick(pygame.display.get_current_refresh_rate() or 60) / 1000  # To get in seconds

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
                camera.resize(*new_size)
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

        if pause:
            continue

        key_handler.tick(dt)
        state.player.tick(dt, move_types)
        state.current_map.tick(dt)
        cam_movement = camera.tick_move(dt)
        state.current_map.background.tick(*cam_movement)

        # Clear window
        window.fill((255, 255, 255))

        # Draw stuff
        camera.render(window)

        # FPS monitor
        window.blit(font_rubik.render(f"FPS: {round(clock.get_fps(), 2)}", True, (0, 0, 0)), (15, 15))

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

        # Update window
        pygame.display.update()


if __name__ == "__main__":
    main()
