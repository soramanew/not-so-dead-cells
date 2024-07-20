import logging
from argparse import ArgumentParser

import pygame
from constants import APP_DESC, APP_NAME
from ui.screens import MainMenu
from util.func import get_project_root


def main():
    parser = ArgumentParser(description=APP_DESC)
    parser.add_argument("--log-level", type=str, default="warning", help="minimum log level to display")
    args = parser.parse_args()

    numeric_log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    logging.basicConfig(
        level=numeric_log_level, format="%(name)s - %(asctime)s - [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )

    pygame.init()

    pygame.display.set_icon(pygame.image.load(get_project_root() / "assets/icon.png"))
    window = pygame.display.set_mode(flags=pygame.RESIZABLE | pygame.FULLSCREEN)
    pygame.display.set_caption(APP_NAME)
    clock = pygame.time.Clock()

    MainMenu(window, clock).main_loop()

    pygame.quit()


if __name__ == "__main__":
    main()
