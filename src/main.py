from __future__ import annotations

import sys

import pygame

import key_handler
from player.player import Player
from map import Map
from camera import Camera
from util_types import PlayerControl


def main():
    pygame.init()

    window_width = 1200
    window_height = 800
    window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    current_map = Map("prisoners_quarters")
    player = Player(current_map, 100, 20)
    camera = Camera(player.movement, window_width, window_height)

    while True:
        dt = clock.tick(60) / 1000  # To get in seconds

        move_types = []

        if key_handler.get(pygame.K_LEFT) or key_handler.get(pygame.K_a):
            move_types.append(PlayerControl.LEFT)
        if key_handler.get(pygame.K_RIGHT) or key_handler.get(pygame.K_d):
            move_types.append(PlayerControl.RIGHT)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                camera.resize(*event.dict["size"])
            elif event.type == pygame.KEYDOWN:
                key_handler.down(event.key)
                if (key_handler.get(pygame.K_s) or key_handler.get(pygame.K_DOWN)) and event.key == pygame.K_SPACE:
                    move_types.append(PlayerControl.SLAM)
                elif event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
                    move_types.append(PlayerControl.JUMP)
                elif event.key == pygame.K_LSHIFT:
                    move_types.append(PlayerControl.ROLL)
            elif event.type == pygame.KEYUP:
                key_handler.up(event.key)

        key_handler.tick(dt)
        player.tick(dt, move_types)
        camera.tick_move(dt)

        # --- Wrapping logic --- #
        # window_width, window_height = window.get_size()
        # if player.left < 0:
        #     player.left += window_width
        # elif player.right > window_width:
        #     player.right -= window_width
        # if player.top < 0:
        #     player.top += window_height
        # elif player.bottom > window_height:
        #     player.bottom -= window_height

        # Clear window
        window.fill((0, 0, 0))

        # Draw stuff
        camera.render(window, current_map, debug=True)

        # Update window
        pygame.display.update()


if __name__ == "__main__":
    main()
