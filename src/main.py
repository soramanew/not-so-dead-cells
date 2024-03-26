from __future__ import annotations

import sys

import pygame

from player2 import Player
from map import Map
from camera import Camera


def main():
    pygame.init()

    window_width = 1200
    window_height = 800
    window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    current_map = Map("prisoners_quarters")
    player = Player(current_map, 100, 20)
    camera = Camera(player, window_width, window_height)

    while True:
        dt = clock.tick(60) / 1000  # To get in seconds

        move_types = []

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_types.append("left")
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_types.append("right")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                camera.resize(*event.dict["size"])
            elif event.type == pygame.KEYDOWN:
                if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and event.key == pygame.K_SPACE:
                    move_types.append("slam")
                elif event.key == pygame.K_SPACE or event.key == pygame.K_w or event.key == pygame.K_UP:
                    move_types.append("jump")
                elif event.key == pygame.K_LSHIFT:
                    move_types.append("roll")

        player.handle_moves(dt, *move_types)
        player.update_position(dt)
        player.tick_changes(dt)
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
