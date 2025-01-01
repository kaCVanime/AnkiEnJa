from .anki_connect import invoke as anki_invoke


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]

def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}