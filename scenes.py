def set_scene(scene):
    mem['game'].scene = scene()


if True:
    from game_files.game import Game
    from login_system.login import LoginScene
    from graphing.history import History
    from mem_hub import mem

    mem.update({'login': LoginScene, 'game_scene': Game, 'history': History})
