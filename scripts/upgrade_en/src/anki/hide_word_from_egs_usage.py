import json
from tqdm import tqdm
from loguru import logger

from anki_connect import invoke as anki_invoke
logger.remove()
logger.add('hide_word_from_egs_usage.log')

def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

def update_examples(nid):
    fields = get_note_fields(nid)
    egs = fields["examples"]
    word = fields["word"]
    while type(egs) == str:
        egs = json.loads(egs)

    examples = egs.copy()

    need_update = False
    for eg in examples:
        if "usage" in eg and word in eg["usage"]:
            eg["usage"] = eg["usage"].replace(word, "~")
            need_update = True

    if need_update:
        note = {
            "id": nid,
            "fields": {
                "examples": json.dumps(examples, ensure_ascii=False)
            }
        }
        anki_invoke("updateNoteFields", note=note)
    return need_update
def main():
    nids = anki_invoke("findNotes", query=r'deck:KEXP2 examples:*usage*')

    for nid in tqdm(nids):
        try:
            update_examples(nid)
        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    main()