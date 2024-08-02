import json
from itertools import chain
from tqdm import tqdm
from loguru import logger
from src.utils import Recorder
from src.anki.anki_connect import invoke as anki_invoke

results_recorder = Recorder()

logger.remove()
logger.add('update_idiom_egs.log', level='INFO', format='{message}')


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

def get_note_tags(nid):
    note = get_note(nid)
    return note["tags"]



@logger.catch
def update_examples(nid, todo):
    egs = todo["examples"]
    while type(egs) == str:
        egs = json.loads(egs)

    for eg in egs:
        if not eg.get("usage", ""):
            eg.pop("usage", None)
        if not eg.get("labels", ""):
            eg.pop("labels", None)
        eg.pop("ai", None)
        eg.pop("en_ai", None)

    logger.info(json.dumps(egs, ensure_ascii=False, indent=4))

    note = {
        "id": nid,
        "fields": {
            "examples": json.dumps(egs, ensure_ascii=False)
        }
    }
    anki_invoke("updateNoteFields", note=note)
def main():
    results_recorder.start()
    todos = list(results_recorder.get_idioms())

    for todo in tqdm(todos):
        try:
            nids = anki_invoke("findNotes", query=f'deck:KEXP2 id:{todo["id"]}')
            assert len(nids) == 2

            for nid in nids:
                update_examples(nid, todo)

        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    main()