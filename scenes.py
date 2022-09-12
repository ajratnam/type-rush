from typing import Type

from utils import BaseScreen


def set_scene(scene: Type[BaseScreen]) -> None:
    """
    It changes the current scene to the scene passed in.

    Args:
      scene (Type[BaseScreen]): The scene to set.
    """
    mem['game'].scene = scene()


if True:
    from game_files.game import Game
    from login_system.login import LoginScene
    from graphing.history import History
    from mem_hub import mem

    mem.update({'login': LoginScene, 'game_scene': Game, 'history': History})
