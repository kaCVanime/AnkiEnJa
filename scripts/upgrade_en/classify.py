import json
from itertools import chain
from zeroshot_topic_classifier.main import classify as get_topic

from src.utils import Recorder

results_recorder = Recorder()

def get_example(item):
    s = item.get('examples')
    if s:
        eg = json.loads(s)
        if eg and (en := eg[0].get('en')):
            return f' Example: "{en}"'
    return ''
def process(item):
    word = item["word"] if "word" in item else item["usage"]
    assert bool(word)

    oald_topics = ','.join(item['topic'].split('=_='))
    s_topic = f"({oald_topics}) " if oald_topics else oald_topics

    definition = item["definition"]
    assert bool(definition)

    example = get_example(item)

    # query = f'{word}: {s_topic}{definition}'
    query = f'{s_topic}{definition}'
    # query = f'"{word}" means "{s_topic}{definition}"'
    # query = f'"{word}" means "{s_topic}{definition}".{example}'
    # query = f'Word:"{word}". Definition:"{s_topic}{definition}".{example}'
    result = get_topic(query, word)

    pass


def main():
    for item in results_recorder.get_idioms():
        process(item)
    pass


if __name__ == '__main__':
    main()