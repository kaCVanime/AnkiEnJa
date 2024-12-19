from itertools import chain
from zeroshot_topic_classifier.main import classify as get_topic

from src.utils import Recorder

results_recorder = Recorder()

def process(item):
    word = item["word"] if "word" in item else item["usage"]
    assert bool(word)

    oald_topics = ','.join(item['topic'].split('=_='))
    s_topic = f"({oald_topics}) " if oald_topics else oald_topics

    definition = item["definition"]
    assert bool(definition)

    # query = f'{word}: {s_topic}{definition}'
    query = f'{s_topic}{definition}'
    result = get_topic(query)

    pass


def main():
    for item in results_recorder.get_all():
        process(item)
    pass


if __name__ == '__main__':
    main()