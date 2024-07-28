import json
from tqdm import tqdm
from loguru import logger

from anki_connect import invoke as anki_invoke
logger.remove()
logger.add('correct_examples.log')

def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

def update_examples(nid):
    fields = get_note_fields(nid)
    egs = fields["examples"]
    while type(egs) == str:
        egs = json.loads(egs)

    if len(egs) > 10:
        ai_egs = [eg for eg in egs if eg.get("ai", False)]
        if len(egs) - len(ai_egs) > 3:
            egs = [eg for eg in egs if not eg.get("ai", False)]
        else:
            egs = [eg for eg in egs if not eg.get("ai", False)].extend(ai_egs[:4])

    for eg in egs:
        if not eg.get("usage", ""):
            eg.pop("usage", None)
        if not eg.get("labels", ""):
            eg.pop("labels", None)
        eg.pop("ai", None)
        eg.pop("en_ai", None)

    note = {
        "id": nid,
        "fields": {
            "examples": json.dumps(egs, ensure_ascii=False)
        }
    }
    anki_invoke("updateNoteFields", note=note)
def main():
    nids = anki_invoke("findNotes", query=r'deck:KEXP2 examples:re:^\"')

    for nid in tqdm(nids):
        try:
            update_examples(nid)
        except Exception as e:
            logger.error(e)

if __name__ == '__main__':
    main()