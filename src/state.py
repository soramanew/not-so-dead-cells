current_map = None
player = None
camera = None
difficulty = 1
score = 0
map_loaded = False


def reset() -> None:
    global current_map, player, camera, difficulty, score, map_loaded
    current_map = None
    player = None
    camera = None
    difficulty = 1
    score = 0
    map_loaded = False
