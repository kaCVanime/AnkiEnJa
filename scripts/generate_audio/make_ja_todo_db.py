import json

from src.utils import anki_invoke, JARecorder
from tqdm.contrib.concurrent import thread_map
from tqdm import tqdm
from loguru import logger

recorder = JARecorder()

logger.remove()
logger.add('make_ja_todo_db.log', level='INFO')


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

def convert_examples(examples):
    return [{"name": e["name"], "ja": e["ja"]} for e in examples]
def update_db(eg_group):
    return recorder.insert_examples(eg_group[0])

def main():
    print('fetching notes...')
    egs = []
    nids = anki_invoke('findNotes', query='deck:KJXP::Read')
    nids = nids[:10]

    for nid in tqdm(nids):
        fields = get_note_fields(nid)
        if fields["examples"]:
            examples = json.loads(fields["examples"])

            egs.append([convert_examples(examples)])

    print('adding to db...')
    thread_map(update_db, egs)

    pass


if __name__ == '__main__':
    recorder.start()
    main()
    recorder.close()