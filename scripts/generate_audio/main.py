from tqdm import tqdm
from loguru import logger

from src.utils import EnRecorder, JaRecorder, anki_invoke, ja_clean, en_clean, get_note_fields

mode = 'en'

logger.remove()
logger.add('main.log')

en_conf = {
    "recorder": EnRecorder(),
    "anki_todos_query": '"deck:KEXP3" -Tag:Synonyms',
    "cleaner": en_clean
}
ja_conf = {
    "recorder": JaRecorder(),
    "anki_todos_query": "deck:KJXP::Read",
    "cleaner": ja_clean
}

conf = en_conf if mode == 'en' else ja_conf


def build_todo_db(recorder):
    print('building todo db')

    query = conf["anki_todos_query"]
    clean = conf["cleaner"]

    nids = anki_invoke('findNotes', query=query)
    for nid in tqdm(nids):
        note = get_note_fields(nid)
        egs = clean(note)
        if egs:
            recorder.add_examples(note["id"], egs)

def main():
    recorder = conf["recorder"]

    if recorder.is_examples_empty():
        build_todo_db(recorder)

    pass

if __name__ == '__main__':
    pass