import pygame
import pygame_gui
from camera import Camera
from map import Map
from player import Player
from util import key_handler
from util.type import PlayerControl


def main():
    pygame.init()

    window_size = 1200, 800
    window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    current_map = Map("prisoners_quarters")
    player = Player(current_map)
    current_map.spawn_enemies(player)
    camera = Camera(player, *window_size)

    ui = pygame_gui.UIManager(window_size)

    font = pygame.font.SysFont("Rubik", 20)

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
                camera.resize(*event.dict["size"])
            elif event.type == pygame.KEYDOWN:
                # TODO changeable keybinds
                key_handler.down(event.key)
                jump = event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP
                if (key_handler.get(pygame.K_s) or key_handler.get(pygame.K_DOWN)) and jump:
                    move_types.append(PlayerControl.SLAM)
                elif jump:
                    move_types.append(PlayerControl.JUMP)
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    move_types.append(PlayerControl.ROLL)
                elif event.key == pygame.K_e:
                    move_types.append(PlayerControl.INTERACT)
                elif event.key == pygame.K_COMMA:
                    move_types.append(PlayerControl.ATTACK_START)
                elif event.key == pygame.K_ESCAPE:
                    pause = not pause
            elif event.type == pygame.KEYUP:
                key_handler.up(event.key)
                if event.key == pygame.K_COMMA:
                    move_types.append(PlayerControl.ATTACK_STOP)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                move_types.append(PlayerControl.ATTACK_START)
            elif event.type == pygame.MOUSEBUTTONUP:
                move_types.append(PlayerControl.ATTACK_STOP)

            ui.process_events(event)

        if pause:
            continue

        key_handler.tick(dt)
        player.tick(dt, move_types)
        current_map.tick(dt)
        camera.tick_move(dt)

        ui.update(dt)

        # Clear window
        window.fill((0, 0, 0))

        # Draw stuff
        camera.render(window, current_map, debug=True)

        # FPS monitor
        window.blit(font.render(f"FPS: {round(clock.get_fps(), 2)}", True, (255, 255, 255)), (15, 15))

        # GUI
        ui.draw_ui(window)

        # Update window
        pygame.display.update()


if __name__ == "__main__":
    main()
