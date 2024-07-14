import logging
from argparse import ArgumentParser

import pygame
from ui import MainMenu
from util.func import get_project_root


def main():
    parser = ArgumentParser(description="A Dead Cells inspired game which is actually not very similar to it.")
    parser.add_argument("--log-level", type=str, default="warning", help="minimum log level to display")
    args = parser.parse_args()

    numeric_log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    logging.basicConfig(
        level=numeric_log_level, format="%(name)s %(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )

    pygame.init()

    pygame.display.set_icon(pygame.image.load(get_project_root() / "assets/icon.png"))
    window = pygame.display.set_mode(flags=pygame.RESIZABLE | pygame.FULLSCREEN)
    pygame.display.set_caption("Not so Dead Cells")
    clock = pygame.time.Clock()

    MainMenu(window, clock)

    pygame.quit()


if __name__ == "__main__":
    main()
