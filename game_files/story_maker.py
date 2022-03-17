import string

stories = []
mapping = {_: _ for _ in string.ascii_letters+' '}


def char_filter(story):
    for pos, char in enumerate(story):
        story[pos] = mapping.get(char, '')
    return ''.join(story)


def parse_stories():
    with open('/home/admin/Projects/Type Rush/stories', 'r') as file:
        return [story.replace('\n', ' ').strip() for story in file.read().split('---')]
