import random
import string
import time

from playsound import playsound

from config import EXIT_SOUND
from game_files.story_maker import parse_stories
from graphing.live import LiveGraph
from scenes import set_scene
from utils import *

left_default_text = Text(LEFT_BUTTON_TEXT, LEFT_BUTTON_COORDS, *BUTTON_SIZE, background_color=LEFT_BUTTON_COLORS[0], font=MediumFont)
LEFT_BUTTON = Button(left_default_text, {'background_color': LEFT_BUTTON_COLORS[1]})
right_default_text = Text(RIGHT_BUTTON_TEXT, RIGHT_BUTTON_COORDS, *BUTTON_SIZE, background_color=RIGHT_BUTTON_COLORS[0], font=MediumFont)
RIGHT_BUTTON = Button(right_default_text, {'background_color': RIGHT_BUTTON_COLORS[1]}, action=lambda: [pygame.display.quit(), playsound(EXIT_SOUND,), stop()])

LOGOUT_BUTTON = RIGHT_BUTTON.modify({'text': 'Logout', 'position': pos(LEFT_BUTTON_COORDS[0], 7 * HEIGHT / 8)})
STATS_BUTTON = LEFT_BUTTON.modify({'text': 'View Stats', 'position': pos(RIGHT_BUTTON_COORDS[0], 7 * HEIGHT / 8)}, action=lambda: set_scene(mem['history']))


class Game(BaseScreen):
    def __init__(self) -> None:
        self.scene_name: str = GAME_NAME
        self.scene = self.draw_outer_scene
        self.score = 0
        self.word = None
        self.wrong = 0
        self.last_call = 0
        self.graph_call = 0
        self.sleep_time = .5
        self.word_rect = None

        story = random.choice(parse_stories())
        self.story = iter(story)

        LEFT_BUTTON.action = self.start_game
        LOGOUT_BUTTON.action = partial(set_scene, mem['login'])

        self.graph = LiveGraph(self, story)

    def draw_outer_scene(self) -> None:
        Text(self.scene_name, (WIDTH/2, HEIGHT/4), font=LargerFont).draw()
        LEFT_BUTTON.draw(self)
        RIGHT_BUTTON.draw(self)
        LOGOUT_BUTTON.draw(self)
        STATS_BUTTON.draw(self)

    def start_game(self) -> None:
        self.scene = self.draw_game
        self.word = self.random_letter

    def draw_graph(self) -> None:
        if (now := time.time()) - self.graph_call > 1:
            self.graph_call = now
            self.graph.plot()

    def draw_game(self) -> None:
        score = Text(f'Your Score: {self.score}', GAME_AREA // 8, font=MediumFont, text_color=Colors.GREY)
        score.draw()
        score.modify(f'Score to Beat: {self.score}', pos(WIDTH * 5 // 6, HEIGHT // 8)).draw()
        self.word_rect = Text(self.word, pos(WIDTH - 25, HEIGHT // 2), font=LargeFont, text_color=Colors.BLUE).draw()
        self.draw_graph()

    @property
    def char(self) -> str:
        if not self.word:
            self.word += self.random_letter
        return self.word[0]

    def handle_keys(self) -> None:
        for event in self.events:
            if event.type == pygame.QUIT:
                stop()
            elif self.word and event.type == pygame.KEYDOWN:
                if event.unicode.casefold() == self.char.casefold():
                    self.score += 1
                    while True:
                        self.word = self.word[1:]
                        if self.char in string.ascii_letters:
                            break
                else:
                    self.wrong += 1

    @property
    def now(self) -> float:
        return time.perf_counter()

    @property
    def random_letter(self) -> str:
        return next(self.story)

    def handler(self) -> None:
        if isinstance(self.word, str) and self.now - self.last_call > self.sleep_time:
            self.word = self.word + self.random_letter
            self.sleep_time -= TEXT_SPEED

            if self.word_rect and self.word_rect.left < 0:
                score = self.score
                self.graph.save()
                self.__init__()
                self.scene_name = f'Your score was {score}'
                LEFT_BUTTON.text = 'Play again!'

            self.last_call = self.now
