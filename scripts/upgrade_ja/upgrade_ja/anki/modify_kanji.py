from tqdm import tqdm

from anki_connect import invoke as anki_invoke

def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]


def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}

def process(nid):
    fields = get_note_fields(nid)
    kanji = fields["kanji"].strip()
    if kanji.startswith("【") and kanji.endswith("】"):
        kanji = kanji[1:-1]
        note = {
            "id": nid,
            "fields": {
                "kanji": kanji
            }
        }
        anki_invoke("updateNoteFields", note=note)

def main():
    nids = anki_invoke("findNotes", query="deck:KJXP kanji:*【*")

    for nid in tqdm(nids):
        process(nid)


if __name__ == '__main__':
    main()