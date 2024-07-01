import pygame
from ui import MainMenu


def main():
    pygame.init()

    window = pygame.display.set_mode(flags=pygame.RESIZABLE | pygame.FULLSCREEN)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    MainMenu(window, clock)


if __name__ == "__main__":
    main()
