from typing import Iterator

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from database_files.database import Score
from game_files.game import Game
from game_files.story_maker import char_filter
from mem_hub import mem

matplotlib.use('Tkagg')
sns.set(style="dark", context="talk")


class LiveGraph:
    def __init__(self, game: Game, story: Iterator[str]) -> None:
        self.game = game
        self.correct = [0, 0, 0]
        self.prev = 0
        self.wrong = []

        word_len = [len(_) for _ in char_filter(list(story)).split()]
        self.rig = 60*len(word_len)//sum(word_len)

        plt.ion()
        plt.close('all')
        self.figure, self.axes = plt.subplots()
        plt.tight_layout()
        plt.show(block=False)

    def plot(self) -> None:
        self.take_screenshot()
        self.axes.clear()
        length = range(max(1, len(self.correct)-9), len(self.correct)+1)
        self.axes.plot(length, self.correct[-10:], color=sns.color_palette("muted", 1)[0], lw=3)
        self.axes.fill_between(length, 0, self.correct[-10:], alpha=.3)
        self.axes.set(ylim=(0, max(self.correct) or 1), xlabel='Time (seconds)', ylabel='WPM')
        plt.pause(.00001)

    def take_screenshot(self) -> None:
        score = (self.game.score-self.prev)*self.rig
        if not score and not (self.correct[-2] == self.correct[-1] == 2) and 0 not in self.correct[:-2]:
            score = 2
        self.correct.append(score)
        self.prev = self.game.score
        self.wrong.append(self.game.wrong)

    def save(self) -> None:
        score = Score(user=mem['user'], score=bytes(self.correct))
        (session := mem['session']).add(score)
        session.commit()
