import pygame
from ui import MainMenu
from util.func import get_project_root


def main():
    pygame.init()

    pygame.display.set_icon(pygame.image.load(get_project_root() / "assets/icon.png"))
    window = pygame.display.set_mode(flags=pygame.RESIZABLE | pygame.FULLSCREEN)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    MainMenu(window, clock)

    pygame.quit()


if __name__ == "__main__":
    main()
