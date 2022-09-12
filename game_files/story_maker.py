import string

from utils import get_path

stories = []
mapping = {_: _ for _ in string.ascii_letters+' '}


def char_filter(story: list[str]) -> str:
    """
    It removes all the non ascii letters.

    Args:
      story (list): The raw story to be filtered.

    Returns:
      str: The story as a single string with the non ascii letters removed.
    """
    for pos, char in enumerate(story):
        story[pos] = mapping.get(char, '')
    return ''.join(story)


def parse_stories() -> list[str]:
    """
    It parses the file in which the stories are written abd splits the contents by the delimiter '---', and finally
    returns a list of the stories.

    Returns:
      list[str]: A list of strings.
    """
    with open(get_path(__name__, 'stories'), 'r') as file:
        return [story.replace('\n', ' ').strip() for story in file.read().split('---')]
