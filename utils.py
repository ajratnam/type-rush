import hashlib
import os
import uuid
from functools import partial
from operator import contains
from threading import Timer
from types import EllipsisType
from typing import Any, Callable, Optional, Collection, Union

from pygame.event import Event
from sqlalchemy import create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.exc import OperationalError
import pygame
from sqlalchemy.orm import Session

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


def get_path(directory: str, file: str) -> str:
    """
    Merges a given directory and a file name to get the path of the file.

    Args:
      directory (str): The directory of the file you want to get the path of.
      file (str): The name of the file you want to open.

    Returns:
      str: The path to the file.
    """
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


def stop() -> None:
    raise


class Text:
    """
    This is the class used everywhere to render text to the screen.

    Attributes:
        text (str/list): The text displayed within the textbox. Can be a string or a list of strings.
        pos (pygame.Vector2/tuple): The position of the textbox on the screen.
        width (int): The width of the textbox.
        height (int): The height of the textbox.
        font (pygame.font.Font): The font of text that will be rendered on the screen.
        background_color (tuple): The background color of the text, a.k.a. the color of the box that the text is within.
        text_color (tuple): The color of the text to be displayed in.
        text_is_centered (bool): Weather the text should be centered within the box. If not, it will be aligned to the top left corner of the box.
        box_is_centered (bool): Weather the box should be centered at the given position. If not, it will be aligned to the top left corner at the postion.
        alpha (int): The transparency of the textbox.
    """
    def __init__(self, text: str | list, position: Optional[pygame.Vector2 | tuple[int, int]] = None, width: int = 0, height: int = 0, font: pygame.font.Font = SmallFont, background_color: Optional[tuple[int, int, int]] = None, text_color: tuple[int, int, int] = TEXT_COLOR, text_is_centered: bool = True, box_is_centered: bool = True, alpha: Optional[int] = None) -> None:
        """
        All initial configuration for the Text object is done here.

        Args:
          text (str/list): The text to be displayed. Can be a string or a list of strings.
          position (pygame.Vector2/tuple, optional): The position of the textbox.
          width (int): The width of the textbox. Defaults to 0
          height (int): The height of the textbox. Defaults to 0
          font (pygame.font.Font): The font that the text will be rendered in.
          background_color (tuple, optional): The color of the box that the text is in.
          text_color (tuple): The color of the text displayed.
          text_is_centered (bool): Weather the text should be centered within the box. If not, it will be aligned to the top left corner. Defaults to True.
          box_is_centered (bool): Weather the box should be centered at the given position. If not, it will be aligned to the top left corner. Defaults to True.
          alpha (int, optional): The transparency of the textbox.
        """
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

    def format(self, text: str | list) -> 'Text':
        """
        Create a new Text object with the same format as the current one, but with a different text.

        Args:
          text (str | list): The new text to be formatted.

        Returns:
          Text: The copied Text object with the new text.
        """
        return self.modify(text)

    def modify(self, text: Optional[str | list] = None, position: Optional[pygame.Vector2 | tuple[int, int]] = None, width: Optional[int] = None, height: Optional[int] = None, font: Optional[pygame.font.Font] = None, background_color: Optional[tuple[int, int, int]] = None, text_color: Optional[tuple[int, int, int]] = None, text_is_centered: Optional[bool] = None, box_is_centered: Optional[bool] = None, alpha: Optional[int] = None) -> 'Text':
        """
        This is used to return a new Text object with the same properties as the original Text object, except for the
        properties that are explicitly changed

        Args:
          text (str/list, optional): The new text to be displayed.
          position (pygame.Vector2/tuple, optional): The new position of the text box.
          width (int, optional): The new width of the text box.
          height (int, optional): The new height of the text box.
          font (pygame.font.Font, optional): The new font of the text.
          background_color (tuple, optional): The new background color of the text box.
          text_color (tuple, optional): The new foreground color of the text.
          text_is_centered (bool, optional): Weather the text should be centered in the box.
          box_is_centered (bool, optional): Weather the box should be centered at the given position.
          alpha (int, optional): The new transparency of the text box.

        Returns:
          Text: A new Text object with the same properties as the original, except for the ones that were changed.
        """
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

    def __add__(self, other: str) -> 'Text':
        """
        Special function invoked when the current Text object is added to a string.

        Args:
          other (str): String to be added at the end of the current text.

        Returns:
          Text: A Text object with the new text added to the right side of the current text
        """
        return self.format(self.text + other)

    def __radd__(self, other: str) -> 'Text':
        """
        Special function invoked when the current Text object is added to a string.

        Args:
          other (str): String to be added at the start of the current text.

        Returns:
          Text: A Text object with the new text added to the left side of the current text
        """
        return self.format(other + self.text)

    def draw(self, should_blit: bool = True) -> pygame.Rect:
        """
        Returns a surface with the text rendered on it, which is immediately drawn to the screen, unless should_blit is
        given as False.

        Args:
          should_blit (bool): Weather the text should be immediately drawn to the screen. Defaults to True.

        Notes:
          if should_blit is False, the surface is returned, and it is the responsibility of the user to blit it to the screen.

        Returns:
          pygame.Rect: The surface with the text rendered on it.
        """
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


class Button:
    """
    This class is used to create buttons.

    Attributes:
      default_text (Text): The text that is displayed on the button when it isn't active.
      active_text (Text/EllipsisType/dict): The text that is displayed on the button when it is active.
      og_text (Text/EllipsisType/dict): The original value passed as the active_text.
      action (function): The function that is triggered when the button is clicked.
    """
    def __init__(self, default_text: Text, active_text: Text | EllipsisType | dict, action: Callable[[], Any] = lambda: None) -> None:
        """
        All initial configuration for the Button is done here.

        Args:
          default_text (Text): The text that will be displayed when the button is not active.
          active_text (Text/EllipsisType/dict): The text that will be displayed when the button is active.
          action (function): The function that will be called when the button is pressed.

        Notes:
            If active_text is Ellipsis, the default_text will be used.
            If active_text is a dict, it will use the key-value pairs and create a new Text object, by modifying the default_text.
            The active state of a Button means that the mouse is hovering over it.
        """
        self.default_text = default_text
        self.active_text = active_text
        self.og_text = active_text
        if not active_text or active_text is ...:
            self.active_text = default_text
        elif isinstance(active_text, dict):
            self.active_text = default_text.modify(**active_text)
        self.action = action

    def draw(self, scene: 'BaseScreen') -> pygame.Rect:
        """
        The handler for drawing the button, it shows different text depending on whether the button is active or not.
        And triggers the action if the button is clicked.

        Args:
          scene (BaseScreen): The scene that the button is being drawn on.

        Returns:
          pygame.Rect: The surface of the button that is being drawn.
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()

        arect = self.active_text.draw

        if arect(False).collidepoint(mouse_x, mouse_y):
            if self.action:
                for event in scene.events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.action()
            return arect()
        return self.default_text.draw()

    def modify(self, default_text: Optional[Text | dict] = None, active_text: Optional[Text | dict] = None, action: Optional[Callable[[], Any]] = None) -> 'Button':
        """
        This method is used to create a new Button object, by modifying the current one.

        Args:
          default_text (Text/dict, optional): The new text that should be displayed when the button is not active.
          active_text (Text/dict, optional): The new text that should be displayed when the button is active.
          action (function, optional): The new function that should be called when the button is pressed.

        Returns:
          Button: A new Button object with the modified attributes.
        """
        default_text = self.default_text if default_text is None else Button(self.default_text, default_text).active_text
        active_text = self.og_text if active_text is None else active_text if not isinstance(active_text, dict) else self.og_text.modify(active_text) if not isinstance(self.og_text, dict) else {**self.og_text, **active_text} if active_text.pop('extend', None) else active_text
        action = self.action if action is None else action
        return Button(default_text, active_text, action)


contains_everything = type('', (), {'__contains__': lambda *_: 1})()


class TextInput:
    """
    The Robust Class to Take Input from the User.

    Attributes:
      question (Text): The question to ask the user.
      size (int): The size of the input box.
      center (bool): Whether the input box should be centered.
      password (bool): Whether the input should be hidden.
      active (bool): Whether the input box is active.
      placeholder (Text): The placeholder text shown when there is no input given by the user inside the textbox.
      min_length (int): The minimum number of characters required by the input.
      max_length (int): The maximum number of characters allowed by the input.
      accepted_chars (str): The list of characters that are allowed by the input.
      verifier (function): The function that verifies whether the given input is valid.
      input (str): Styling for input given by the user.
      current (str): The active TextInput in the group.
      group (list): The list of TextInputs in the group.
    """
    def __init__(self, question: Text, _input: Optional[Text | dict] = None, placeholder: Text | str | dict = '', password: bool = False, active: bool = False, _prev: Optional['TextInput'] = None, _next: Optional['TextInput'] = None, min_length: int = 0, max_length: float = float('inf'), accepted_chars: Collection[str] = contains_everything, verifier: Optional[Callable[[str], bool]] = None) -> None:
        """
        All initial configuration for the TextInput is done here.

        Args:
          question (Text): The question to be asked.
          _input (Optional[Text | dict]): The configuration of the text entered by the user.
          placeholder (Text | str | dict): The text that will be displayed when the input is empty.
          password (bool): If True, the input will be hidden. Defaults to False
          active (bool): Whether the input is active or not. Defaults to False
          _prev (TextInput, optional): The previous TextInput to be linked to in the group.
          _next (TextInput, optional): The next TextInput to be linked to in the group.
          min_length (int): The minimum number of characters required for the input. Defaults to 0
          max_length (float): The maximum number of characters that can be entered. Defaults to Infinite
          accepted_chars (Collection[str]): A collection of characters that are allowed to be entered.
          verifier (function, optional): A function that takes in the input and returns True if the input is correct.
        """
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

    def verify(self) -> bool:
        """
        It checks if the input is valid

        Returns:
          bool: Weather the input is valid or not.
        """
        res = ''.join(self.input.text)
        if len(res) < self.min_length:
            return self.show_error(f'Minimum atleast {self.min_length} character{" is" if self.min_length == 1 else "s are"} required')
        if len(res) > self.max_length:
            return self.show_error(f'Only maximum {self.max_length} characters are allowed')
        if not all(map(partial(contains, res), res)):
            return False
        return self.verifier(res)

    def show_error(self, text: str) -> bool | None:
        """
        Temporarily shows an error message in the input box.

        Args:
          text (str): The error message to be shown.

        Returns:
          bool: Weather the error message was displayed or not.
        """
        if not hasattr(self, 'error'):
            old = self.input
            self.deactivate()
            self.input = self.input.modify(list(text), text_color=Colors.RED)
            password, self.password = self.password, False
            setattr(self, 'error', True)
            Timer(.3, lambda: [setattr(self, 'input', self.input.modify(text_color=Colors.BRIGHT_RED)), Timer(.3, lambda: [setattr(self, 'password', password), setattr(self, 'input', old), self.set_active(), hasattr(self, 'error') and delattr(self, 'error')]).start()]).start()
            return False

    @property
    def cursor_pos(self) -> int:
        """
        It returns the position of the cursor in the input box.

        Returns:
          int: Position of the cursor in the input box.
        """
        return len(self.input.text) if self._cursor_pos is None else self._cursor_pos

    @cursor_pos.setter
    def cursor_pos(self, value: int) -> None:
        """
        The function which is triggered when the cursor position is changed.
        It also keeps the cursor in the range of the input box.

        Args:
          value (int): The new position of the cursor.
        """
        self._cursor_pos = min(max(value, 0), len(self.input.text)) if isinstance(value, int) else None

    @property
    def cursor(self) -> str:
        """
        Returns the cursor character or an empty string depending on frame count, giving the illusion of blinking.

        Returns:
          str: The character for the cursor.
        """
        self._cursor += 1
        self._cursor %= FPS
        return self.active and '|' * (self._cursor < FPS / 2) or ''

    @property
    def text(self) -> 'Text':
        """
        Returns the text as per the style of the input box. Also replaces the text with '*' if the input is a password.

        Returns:
          Text: The text object displayed in the input box.
        """
        actual_input = ['*'] * len(self.input.text) if self.password else self.input.text
        return self.input.format(''.join(actual_input[:self.cursor_pos] + [self.cursor] + actual_input[self.cursor_pos:])) if actual_input else self.cursor + self.placeholder

    def is_at_pos(self, index: int) -> bool:
        """
        Checks weather the TextInput is at the given index in the group.

        Args:
          index (int): The index of the group to check.

        Returns:
          Weather the TextInput is at the specified index in the group.
        """
        return self.group[index] is self

    def pop_back(self) -> None:
        """
        It removes the character which is before the cursors position. Functionality for the backspace key.
        """
        if self.cursor_pos:
            self.input.text.pop(self.cursor_pos - 1)
            self.cursor_pos -= 1

    def pop_front(self) -> None:
        """
        It removes the character at the cursor position. Functionality for the delete key.
        """
        if 0 <= self.cursor_pos + 1 <= len(self.input.text):
            self.input.text.pop(self.cursor_pos)

    def add_char(self, char: str) -> None:
        """
        It inserts a character into the input text at the current cursor position.

        Args:
          char (str): The character to add to the input.
        """
        self.input.text.insert(self.cursor_pos, char)
        self.cursor_pos += 1

    def set_next(self, text_input: 'TextInput') -> None:
        """
        It sets the given TextInput as the next TextInput in the group.

        Args:
          text_input (TextInput): The TextInput object to add to the group.
        """
        self.group.append(text_input)
        if self.current:
            text_input.active = False
        elif text_input.active:
            self.current[0] = text_input
        text_input.group = self.group
        text_input.current = self.current

    @property
    def index(self) -> int:
        """
        It returns the position of the TextInput in the group.

        Returns:
          int: Index of the current instance in the group.
        """
        return self.group.index(self)

    @property
    def next(self) -> 'TextInput':
        """
        It returns the next TextInput in the group.

        Returns:
          TextInput: The next TextInput object in the group.
        """
        if self.index < len(self.group) - 1:
            return self.group[self.index + 1]

    @property
    def prev(self) -> 'TextInput':
        """
        It returns the previous TextInput in the group.

        Returns:
          TextInput: The previous TextInput object in the group.
        """
        if self.index > 0:
            return self.group[self.index - 1]

    def __len__(self) -> int:
        """
        It returns the length of the input text.

        Returns:
          int: Number of characters in the input.
        """
        return len(self.input.text)

    def __bool__(self) -> bool:
        """
        Returns weather the input text is not empty.

        Returns:
          bool: Weather the input text contains atleast one character.
        """
        return True

    def set_next_active(self) -> None:
        """
        It activates the next TextInput in the group.
        """
        self.current[0] = None
        if _next := self.next:
            _next.set_active()
        self.active = False

    def set_prev_active(self) -> None:
        """
        It activates the previous TextInput in the group.
        """
        self.current[0] = None
        if _prev := self.prev:
            _prev.set_active()
        self.active = False

    def set_active(self) -> None:
        """
        It activates itself.
        """
        self.active = True
        if self.current[0] and self.current[0] is not self:
            self.current[0].active = False
        self.current[0] = self

    def deactivate(self) -> None:
        """
        It deactivates itself.
        """
        if self.current[0]:
            self.current[0].active = False
        self.current[0] = None

    def draw(self, scene: 'BaseScreen') -> None:
        """
        It draws the textbox and handles the keyboard events.

        Args:
          scene (BaseScreen): The screen that the textbox is being drawn on.
        """
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
    """
    The Base class for all scenes.

    Attributes:
      events (list): The list of events that happened in the scene.
      screen (function): The screen that the scene is drawn on.
      handler (function): The handler which handles the remaining events.
    """
    scene: Callable[[], Any] = lambda _: _
    handler: Callable[[], Any] = lambda _: _
    events: list[Event] = []

    def reset(self) -> None:
        """
        It resets the scene to its initial state
        """
        self.__init__()

    def handle_keys(self) -> None:
        """
        The abstract method for handling keys.
        """
        for event in self.events:
            if event.type == pygame.QUIT:
                stop()

    def main_loop(self) -> None:
        """
        The abstract method for the main loop, which is called every frame.
        """
        screen.fill(SCREEN_COLOR)

        self.events = list(pygame.event.get())
        self.handle_keys()
        self.scene()
        self.handler()

        pygame.display.update()
        clock.tick(FPS)


def try_connect(database: str) -> Engine:
    """
    It tries to connect to a database, and returns the engine object if it succeeds.

    Args:
      database (str): The address of the database.

    Returns:
      Engine: The engine object which is connected to the database.
    """
    try:
        engine = create_engine(database, echo=False)
        with engine.connect():
            return engine
    except OperationalError:
        pass


def encrypt_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    It hashes the password with the salt and then encrypts it with the sha1 algorithm.

    Args:
      password (str): The password to be encrypted.
      salt (Optional[str]): A random string of characters that is used to make the password more secure.

    Returns:
      tuple[str, str]: A tuple of the encrypted hashed password and the salt.
    """
    salt = salt if salt else uuid.uuid4().hex
    return hashlib.sha1((password + salt).encode()).hexdigest(), salt


def set_value(ctx: DefaultExecutionContext) -> str | None:
    """
    It encrypts the password automatically when the user is created.

    Args:
      ctx (DefaultExecutionContext): The context of the query

    Returns:
      str: The salt which was used to encrypt the password.
    """
    ctx = ctx.current_parameters
    if not ctx['password']:
        return
    ctx['password'], salt = encrypt_password(ctx['password'])
    return salt


def make_user_id() -> str:
    """
    Query the database to get the last user id and increment it by 1.

    Returns:
      str: The next user id.
    """
    uid = mem['session'].query(mem['User'].id, func.max(mem['User'].id)).first()[-1]
    return f'user{uid + 1}'


def get_user(session: Session, user: 'User') -> Union['User', None]:
    """
    Get a user from the database, if it exists.

    Args:
      session (Session): The session object that is used to query the database.
      user (User): The dummy user object, which isn't initialized from the database.

    Returns:
      User: The user object that is initialized from the database.
    """
    player = session.query(user.__class__).filter_by(username=user.username).all()
    return player[0] if player else None


if True:
    from database_files.database import User
