import string

from utils import get_path

stories = []
mapping = {_: _ for _ in string.ascii_letters+' '}


def char_filter(story):
    for pos, char in enumerate(story):
        story[pos] = mapping.get(char, '')
    return ''.join(story)


def parse_stories():
    with open(get_path(__name__, 'stories'), 'r') as file:
        return [story.replace('\n', ' ').strip() for story in file.read().split('---')]
