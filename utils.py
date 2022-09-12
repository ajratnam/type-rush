import hashlib
import os
import uuid
from functools import partial
from operator import contains
from threading import Timer

from sqlalchemy import create_engine, func
from sqlalchemy.exc import OperationalError
import pygame
from mem_hub import mem


class Colors:
    BLACK = 0, 0, 0
    WHITE = 255, 255, 255
    GREEN = 0, 150, 0
    RED = 150, 0, 0
    BRIGHT_GREEN = 0, 255, 0
    BRIGHT_RED = 255, 0, 0
    BLUE = 9, 167, 224
    BRIGHT_BLUE = 79, 237, 255
    YELLOW = 147, 147, 0
    GREY = 170, 170, 170


def get_path(directory, file):
    return os.path.join(os.path.dirname(directory), file)


pos = partial(pygame.Vector2)

if True:
    from game_files.config import *

pygame.init()
screen = pygame.display.set_mode(DIMENSIONS)
icon = pygame.image.load(ICON_PATH)
pygame.display.set_icon(icon)
clock = pygame.time.Clock()

draw_rect = partial(pygame.draw.rect, screen)

Font = partial(pygame.font.Font, FONT_PATH)
SmallFont = Font(SMALL_FONT_SIZE)
MediumFont = Font(MEDIUM_FONT_SIZE)
LargeFont = Font(LARGE_FONT_SIZE)
LargerFont = Font(LARGER_FONT_SIZE)
GAME_AREA = pygame.Vector2(DIMENSIONS)


def stop():
    raise


class Button:
    def __init__(self, default_text, active_text, action=lambda: None):
        self.default_text = default_text
        self.active_text = active_text
        self.og_text = active_text
        if not active_text or active_text is ...:
            self.active_text = default_text
        elif isinstance(active_text, dict):
            self.active_text = default_text.modify(**active_text)
        self.action = action

    def draw(self, scene):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        arect = self.active_text.draw

        if arect(False).collidepoint(mouse_x, mouse_y):
            if self.action:
                for event in scene.events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.action()
            return arect()
        return self.default_text.draw()

    def modify(self, default_text=None, active_text=None, action=None):
        default_text = self.default_text if default_text is None else Button(self.default_text, default_text).active_text
        active_text = self.og_text if active_text is None else active_text if not isinstance(active_text, dict) else self.og_text.modify(active_text) if not isinstance(self.og_text, dict) else {**self.og_text, **active_text} if active_text.pop('extend', None) else active_text
        action = self.action if action is None else action
        return Button(default_text, active_text, action)


class Text:
    def __init__(self, text, position=None, width=0, height=0, font=SmallFont, background_color=None,
                 text_color=TEXT_COLOR, text_is_centered=True, box_is_centered=True, alpha=None):
        self.text = text
        self.pos = position
        self.width = width
        self.height = height
        self.font = font
        self.background_color = background_color
        self.text_color = text_color
        self.text_is_centered = text_is_centered
        self.box_is_centered = box_is_centered
        self.alpha = alpha

    def format(self, text):
        return self.modify(text)

    def modify(self, text=None, position=None, width=None, height=None, font=None, background_color=None,
               text_color=None, text_is_centered=None, box_is_centered=None, alpha=None):
        text = self.text if text is None else text
        position = self.pos if position is None else position
        width = self.width if width is None else width
        height = self.height if height is None else height
        font = self.font if font is None else font
        background_color = self.background_color if background_color is None else background_color
        text_color = self.text_color if text_color is None else text_color
        text_is_centered = self.text_is_centered if text_is_centered is None else text_is_centered
        box_is_centered = self.box_is_centered if box_is_centered is None else box_is_centered
        alpha = self.alpha or alpha
        return Text(text, position, width, height, font, background_color, text_color, text_is_centered,
                    box_is_centered, alpha)

    def __add__(self, other):
        return self.format(self.text + other)

    def __radd__(self, other):
        return self.format(other + self.text)

    def draw(self, should_blit=True):
        surf = self.font.render(self.text, True, self.text_color)
        if self.alpha:
            surf.set_alpha(self.alpha)
        rect = bg_rect = surf.get_rect()

        if self.box_is_centered:
            rect.center = self.pos
        else:
            rect.topleft = self.pos

        if self.background_color:
            width = max(self.width, rect.width)
            height = max(self.height, rect.height)
            bg_rect = pygame.Rect(self.pos.xy, (width, height))
            if self.box_is_centered:
                bg_rect.center = self.pos
            if self.text_is_centered:
                rect.center = bg_rect.center
            else:
                bg_rect.topleft = rect.topleft

        if should_blit:
            if self.background_color:
                draw_rect(self.background_color, bg_rect)
            screen.blit(surf, rect)
        return bg_rect if self.background_color else rect


contains_everything = type('', (), {'__contains__': lambda *_: 1})()


class TextInput:
    def __init__(self, question, _input=None, placeholder='', password=False, active=False, _prev=None, _next=None,
                 min_length=0, max_length=float('inf'), accepted_chars=contains_everything, verifier=None):
        self.question = question
        self.size = question.width, question.height
        self.center = question.pos.xy
        self.password = password
        self.active = active
        self.placeholder = question.format(placeholder) if isinstance(placeholder, str) else question.modify(**placeholder) if isinstance(placeholder, dict) else placeholder
        self.min_length = min_length
        self.max_length = max_length
        self.accepted_chars = accepted_chars
        self.verifier = verifier or (lambda _: True)

        self.input = question.modify(**_input).format([]) if isinstance(_input, dict) else _input.format([]) if _input else question.format([])
        self.current = [self if active else None]
        self.group = [self]
        self._cursor = 0
        self._cursor_pos = None

        if _prev:
            _prev.set_next(self)

        if _next:
            self.set_next(_next)

    def verify(self):
        res = ''.join(self.input.text)
        if len(res) < self.min_length:
            return self.show_error(f'Minimum atleast {self.min_length} character{" is" if self.min_length == 1 else "s are"} required')
        if len(res) > self.max_length:
            return self.show_error(f'Only maximum {self.max_length} characters are allowed')
        if not all(map(partial(contains, res), res)):
            return False
        return self.verifier(res)

    def show_error(self, text):
        if not hasattr(self, 'error'):
            old = self.input
            self.deactivate()
            self.input = self.input.modify(list(text), text_color=Colors.RED)
            password, self.password = self.password, False
            setattr(self, 'error', True)
            Timer(.3, lambda: [setattr(self, 'input', self.input.modify(text_color=Colors.BRIGHT_RED)), Timer(.3, lambda: [setattr(self, 'password', password), setattr(self, 'input', old), self.set_active(), hasattr(self, 'error') and delattr(self, 'error')]).start()]).start()
            return False

    @property
    def cursor_pos(self):
        return len(self.input.text) if self._cursor_pos is None else self._cursor_pos

    @cursor_pos.setter
    def cursor_pos(self, value):
        self._cursor_pos = min(max(value, 0), len(self.input.text)) if isinstance(value, int) else None

    @property
    def cursor(self):
        self._cursor += 1
        self._cursor %= FPS
        return self.active and '|' * (self._cursor < FPS / 2) or ''

    @property
    def text(self):
        actual_input = ['*'] * len(self.input.text) if self.password else self.input.text
        return self.input.format(''.join(actual_input[:self.cursor_pos] + [self.cursor] + actual_input[self.cursor_pos:])) if actual_input else self.cursor + self.placeholder

    def is_at_pos(self, pos):
        return self.group[pos] is self

    def pop_back(self):
        if self.cursor_pos:
            self.input.text.pop(self.cursor_pos - 1)
            self.cursor_pos -= 1

    def pop_front(self):
        if 0 <= self.cursor_pos + 1 <= len(self.input.text):
            self.input.text.pop(self.cursor_pos)

    def add_char(self, char):
        self.input.text.insert(self.cursor_pos, char)
        self.cursor_pos += 1

    def set_next(self, text_input):
        self.group.append(text_input)
        if self.current:
            text_input.active = False
        elif text_input.active:
            self.current[0] = text_input
        text_input.group = self.group
        text_input.current = self.current

    @property
    def index(self):
        return self.group.index(self)

    @property
    def next(self):
        if self.index < len(self.group) - 1:
            return self.group[self.index + 1]

    @property
    def prev(self):
        if self.index > 0:
            return self.group[self.index - 1]

    def __len__(self):
        return len(self.input.text)

    def __bool__(self):
        return True

    def set_next_active(self):
        self.current[0] = ''
        if _next := self.next:
            _next.set_active()
        self.active = False

    def set_prev_active(self):
        self.current[0] = ''
        if _prev := self.prev:
            _prev.set_active()
        self.active = False

    def set_active(self):
        self.active = True
        if self.current[0] and self.current[0] is not self:
            self.current[0].active = False
        self.current[0] = self

    def deactivate(self):
        if self.current[0]:
            self.current[0].active = False
        self.current[0] = ''

    def draw(self, scene):
        button = Button(self.question, ..., self.set_active)
        rect = button.draw(scene)
        button.modify(self.text.modify(position=pos(rect.topright), width=self.text.width - rect.width, background_color=SCREEN_COLOR, text_is_centered=False, box_is_centered=False), ...).draw(scene)

        if self.active:
            for event in scene.events:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN, pygame.K_DOWN]:
                        self.set_next_active()
                        scene.events.clear()
                    elif event.key == pygame.K_BACKSPACE:
                        self.pop_back()
                    elif event.key == pygame.K_DELETE:
                        self.pop_front()
                    elif event.key == pygame.K_LEFT:
                        self.cursor_pos -= 1
                    elif event.key == pygame.K_RIGHT:
                        self.cursor_pos += 1
                    elif event.key == pygame.K_HOME:
                        self.cursor_pos = 0
                    elif event.key == pygame.K_END:
                        self.cursor_pos = None
                    elif event.key == pygame.K_UP:
                        self.set_prev_active()
                        scene.events.clear()
                    elif char := event.unicode:
                        if char not in self.accepted_chars:
                            self.show_error(f'Only letters or numbers or underscore!!')
                        elif len(self) == self.max_length:
                            self.show_error(f'Maximum only {self.max_length} characters!!')
                        else:
                            self.add_char(char)
        elif not self.current[0]:
            for event in scene.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP and self.is_at_pos(-1) or event.key == pygame.K_DOWN and self.is_at_pos(0):
                        self.set_active()


class BaseScreen:
    scene = handler = lambda _: _
    events = []

    def reset(self):
        self.__init__()

    def handle_keys(self):
        for event in self.events:
            if event.type == pygame.QUIT:
                stop()

    def main_loop(self):
        screen.fill(SCREEN_COLOR)

        self.events = list(pygame.event.get())
        self.handle_keys()
        self.scene()
        self.handler()

        pygame.display.update()
        clock.tick(FPS)


def try_connect(database):
    try:
        engine = create_engine(database, echo=False)
        with engine.connect():
            return engine
    except OperationalError:
        pass


def encrypt_password(password, salt=None):
    salt = salt if salt else uuid.uuid4().hex
    return hashlib.sha1((password + salt).encode()).hexdigest(), salt


def set_value(ctx):
    ctx = ctx.current_parameters
    if not ctx['password']:
        return
    ctx['password'], salt = encrypt_password(ctx['password'])
    return salt


def make_user_id():
    uid = mem['session'].query(mem['User'].id, func.max(mem['User'].id)).first()[-1]
    return f'user{uid + 1}'


def get_user(session, user):
    player = session.query(user.__class__).filter_by(username=user.username).all()
    return player[0] if player else None
