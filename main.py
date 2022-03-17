from threading import Thread

from playsound import playsound

from config import WELCOME_SOUND
from database_files.action import setup_database
from database_files.database import Session, engine
from mem_hub import mem

from login_system.login import LoginScene


class Game:
    scene = LoginScene()


Thread(target=playsound, args=(WELCOME_SOUND,)).start()


game = Game()
session = Session()
conn = engine.connect()
try:
    mem['session'] = session
    mem['conn'] = conn
    mem['game'] = game

    setup_database(session)

    while 1:
        game.scene.main_loop()
finally:
    session.close()
    conn.close()
    mem.clear()
