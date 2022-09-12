import math

import numpy as np
import pygame
from matplotlib import pyplot as plt
from matplotlib.backends import backend_agg
from numpy import linspace

from database_files.database import Score
from game_files.config import HEIGHT, WIDTH, BUTTON_SIZE
from mem_hub import mem
from scenes import set_scene
from utils import BaseScreen, Button, Text, pos, Colors, screen, GAME_AREA, Font, SmallFont


def history_iterator():
    yield from (
        mem['session'].query(Score)
        .filter_by(user_id=mem['user'].id)
        .order_by(Score.date_created.desc()).all()
    )


BACK_BUTTON_MAIN = Button(Text('Go Back', pos(WIDTH/2, 3*HEIGHT/4), *BUTTON_SIZE, background_color=Colors.RED, font=Font(60)), {'background_color': Colors.BRIGHT_RED}, action=lambda: set_scene(mem['game_scene']))
BACK_BUTTON_SUB = BACK_BUTTON_MAIN.modify({'box_is_centered': False, 'position': pos(20, 3*HEIGHT/8)})
PREV_BUTTON = BACK_BUTTON_MAIN.modify({'text': 'Previous', 'position': pos(WIDTH/4, 3*HEIGHT/4), 'background_color': Colors.GREEN}, {'background_color': Colors.BRIGHT_GREEN, 'extend': True})
NEXT_BUTTON = PREV_BUTTON.modify({'text': 'Next', 'position': 3*GAME_AREA/4})
COMPARE_BUTTON = NEXT_BUTTON.modify({'box_is_centered': False, 'text': 'Compare', 'position': pos(20, 5*HEIGHT/8)})
STOP_COMPARE_BUTTON = BACK_BUTTON_MAIN.modify({'box_is_centered': False, 'font': SmallFont, 'text': 'Stop Comparing graph', 'position': pos(20, HEIGHT/2)})


class History(BaseScreen):
    history: list
    index: int
    score: Score
    page = 0
    original_score = None

    def __init__(self):
        PREV_BUTTON.action = lambda: setattr(self, 'page', self.page - 1)
        NEXT_BUTTON.action = lambda: setattr(self, 'page', self.page + 1)
        BACK_BUTTON_SUB.action = lambda: setattr(self, 'scene', self.show_history)
        COMPARE_BUTTON.action = lambda: [setattr(self, 'original_score', self.score), setattr(self, 'scene', self.show_history)]
        STOP_COMPARE_BUTTON.action = lambda: [setattr(self, 'original_score', None), lambda: setattr(self, 'scene', self.show_history)]

    def show_history(self):
        if not hasattr(self, 'history'):
            self.history = list(history_iterator())

        if tot := len(rows := self.history[20*self.page: 20*(self.page+1)]):
            ncols = math.ceil(math.sqrt(tot))
            nrows = math.ceil(tot/ncols)

            for nrow, y in enumerate(linspace(0, WIDTH, nrows+2)[1:-1]):
                curr = rows[ncols*nrow:ncols*(nrow+1)]
                for ncol, x in enumerate(linspace(0, 3*HEIGHT/4, len(curr)+2)[1:-1]):
                    Button(Text(f'{curr[ncol].date_created}', pos(y, x)), {'text_color': Colors.BRIGHT_BLUE}, action=lambda: self.toggle(ncols*nrow+ncol)).draw(self)

        BACK_BUTTON_MAIN.draw(self)
        if self.page > 0:
            PREV_BUTTON.draw(self)
        if self.page < self.pages - 1:
            NEXT_BUTTON.draw(self)

    def create_graph(self):
        plt.ioff()
        plt.close('all')
        figure, axes = plt.subplots()
        plt.tight_layout()

        correct = np.array(list(self.score.score))
        axes.clear()
        length = range(1, correct.size + 1)
        max_score = np.max(correct)

        if self.original_score:
            main = np.array(list(self.original_score.score))
            if correct.size > main.size:
                correct = correct[:main.size]
                length = range(1, main.size + 1)
            else:
                main = main[:correct.size]

            if (og_max := np.max(main)) > max_score:
                max_score = og_max

            axes.fill_between(
                length, main, correct, where=(correct > main),
                interpolate=True, color="green", alpha=0.25,
                label="Fast"
            )
            axes.fill_between(
                length, main, correct, where=(correct <= main),
                interpolate=True, color="red", alpha=0.25,
                label="Slow"
            )
            axes.legend()
        else:
            axes.plot(length, correct, color='blue', lw=3)
            axes.fill_between(length, 0, correct, alpha=.3)
        axes.set(ylim=(0, max_score or 1), xlabel='Time (seconds)', ylabel='WPM')

        (canvas := backend_agg.FigureCanvasAgg(figure)).draw()
        raw_data = canvas.get_renderer().tostring_rgb()
        size = canvas.get_width_height()

        return pygame.image.fromstring(raw_data, size, "RGB"), pos(*size)

    @property
    def pages(self):
        return math.ceil(self.count / 20)

    def graph(self):
        screen.blit(self.surf, ((GAME_AREA - self.size)/2).xy)
        if self.original_score:
            STOP_COMPARE_BUTTON.draw(self)
        else:
            BACK_BUTTON_SUB.draw(self)
            COMPARE_BUTTON.draw(self)

    def toggle(self, score):
        self.index = score
        self.score = self.history[score]
        self.surf, self.size = self.create_graph()
        self.scene = self.graph

    @property
    def count(self):
        return len(self.history)

    scene = show_history
