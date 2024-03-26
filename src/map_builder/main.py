import pygame

from map_builder.builder import Builder


def main():
    pygame.init()

    window_width = 1200
    window_height = 800
    window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("Not so Dead Cells - Map Builder")
    builder = Builder(window, "prisoners_quarters", 2000, 2000)  # TODO: make selector for literals
    builder.main_loop()


if __name__ == "__main__":
    main()
