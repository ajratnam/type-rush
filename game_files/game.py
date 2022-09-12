import random
import string
import time
from typing import Iterator

from playsound import playsound

from config import EXIT_SOUND
from game_files.story_maker import parse_stories
from scenes import set_scene
from utils import *

left_default_text = Text(LEFT_BUTTON_TEXT, LEFT_BUTTON_COORDS, *BUTTON_SIZE, background_color=LEFT_BUTTON_COLORS[0], font=MediumFont)
LEFT_BUTTON = Button(left_default_text, {'background_color': LEFT_BUTTON_COLORS[1]})
right_default_text = Text(RIGHT_BUTTON_TEXT, RIGHT_BUTTON_COORDS, *BUTTON_SIZE, background_color=RIGHT_BUTTON_COLORS[0], font=MediumFont)
RIGHT_BUTTON = Button(right_default_text, {'background_color': RIGHT_BUTTON_COLORS[1]}, action=lambda: [pygame.display.quit(), playsound(EXIT_SOUND,), stop()])

LOGOUT_BUTTON = RIGHT_BUTTON.modify({'text': 'Logout', 'position': pos(LEFT_BUTTON_COORDS[0], 7 * HEIGHT / 8)})
STATS_BUTTON = LEFT_BUTTON.modify({'text': 'View Stats', 'position': pos(RIGHT_BUTTON_COORDS[0], 7 * HEIGHT / 8)}, action=lambda: set_scene(mem['history']))


class Game(BaseScreen):
    """
    Attributes:
        scene_name (str): The name of the game.
        scene (Callable[[], None]): The current scene.
        score (int): The current score of the player.
        word (str | None): The current word being typed.
        wrong (int): The number of wrong guesses.
        last_call (float): The time when the letter had last been added.
        graph_call (float): The time when the graph had last updated.
        sleep_time (float): The delay before adding a new letter to the story.
        word_rect (Text | None): The text object of the word.
        story (Iterator[str]): The story on the screen to be typed.
        graph (LiveGraph): The interactive graph, which shows the users typing speed.
    """
    def __init__(self) -> None:
        """
        Initializes and sets the game scene ready for action.
        """
        self.scene_name: str = GAME_NAME
        self.scene: Callable[[], None] = self.draw_outer_scene
        self.score: int = 0
        self.word: str | None = None
        self.wrong: int = 0
        self.last_call: float = 0
        self.graph_call: float = 0
        self.sleep_time: float = .5
        self.word_rect: Text | None = None

        story = random.choice(parse_stories())
        self.story: Iterator[str] = iter(story)

        LEFT_BUTTON.action = self.start_game
        LOGOUT_BUTTON.action = partial(set_scene, mem['login'])

        self.graph: LiveGraph = LiveGraph(self, story)

    def draw_outer_scene(self) -> None:
        """
        This function draws the menu of the game, which has the play button,
        the quit button, the logout button and the stats button.
        """
        Text(self.scene_name, (WIDTH/2, HEIGHT/4), font=LargerFont).draw()
        LEFT_BUTTON.draw(self)
        RIGHT_BUTTON.draw(self)
        LOGOUT_BUTTON.draw(self)
        STATS_BUTTON.draw(self)

    def start_game(self) -> None:
        """
        Set this class as the current scene, and prepare the word.
        """
        self.scene = self.draw_game
        self.word = self.next_letter

    def draw_graph(self) -> None:
        """
        Update the graph if it's been more than one second.
        """
        if (now := time.time()) - self.graph_call > 1:
            self.graph_call = now
            self.graph.plot()

    def draw_game(self) -> None:
        """
        Draw the scores, and update the graph.
        """
        score = Text(f'Your Score: {self.score}', GAME_AREA // 8, font=MediumFont, text_color=Colors.GREY)
        score.draw()
        score.modify(f'Score to Beat: {self.score}', pos(WIDTH * 5 // 6, HEIGHT // 8)).draw()
        self.word_rect = Text(self.word, pos(WIDTH - 25, HEIGHT // 2), font=LargeFont, text_color=Colors.BLUE).draw()
        self.draw_graph()

    @property
    def char(self) -> str:
        """
        If the word is empty, add a random letter to it.
        Then return the first letter of the word.

        Returns:
          str: The first letter of the word.
        """
        if not self.word:
            self.word += self.next_letter
        return self.word[0]

    def handle_keys(self) -> None:
        """
        Handle the key presses and check if the key pressed is the same as the first letter of the word.
        If it is, remove the first letter of the word and increase the score.
        If it is not, increase the number of wrong guesses.
        """
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
        """
        A wrapper for the time.time() function within the class as a descriptor, for easier access.

        Returns:
          float: The current time in seconds since the Epoch.
        """
        return time.time()

    @property
    def next_letter(self) -> str:
        """
        Fetch the next letter in the story.

        Returns:
          str: The next letter from the story.
        """
        return next(self.story)

    def handler(self) -> None:
        """
        Add the next letter from the story in every specified interval, and increase the game speed.
        And end the game if the word has gone off the screen.
        """
        if isinstance(self.word, str) and self.now - self.last_call > self.sleep_time:
            self.word = self.word + self.next_letter
            self.sleep_time -= TEXT_SPEED

            if self.word_rect and self.word_rect.left < 0:
                score = self.score
                self.graph.save()
                self.__init__()
                self.scene_name = f'Your score was {score}'
                LEFT_BUTTON.text = 'Play again!'

            self.last_call = self.now


if True:
    from graphing.live import LiveGraph
