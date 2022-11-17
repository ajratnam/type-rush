from typing import Type
from mem_hub import mem
from utils import BaseScreen


def set_scene(scene: Type[BaseScreen]) -> None:
    mem['game'].scene = scene()


if True:
    from game_files.game import Game
    from login_system.login import LoginScene
    from graphing.history import History

    mem.update({'login': LoginScene, 'game_scene': Game, 'history': History})
