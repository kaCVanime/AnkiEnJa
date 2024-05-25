import logging
from anki_connect import invoke as anki_invoke
from tqdm import tqdm
from main import get_note_fields, get_note_ids_from_last, get_last_note_id, set_last_note_id

logger = logging.getLogger(__name__)


def run():
    logging.basicConfig(
        filename="transform_brief.log",
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )

    nids = anki_invoke("findNotes", query="deck:KEXP::Read brief:re:.+")

    for nid in tqdm(nids):
        note = get_note_fields(nid)
        brief = note["brief"]
        id = note["id"]
        tnids = anki_invoke("findNotes", query=f"deck:KEXP::Write id:{id}")
        if len(tnids):
            tnid = tnids[0]
            obj = {"id": tnid, "fields": { "brief": brief }}
            anki_invoke("updateNoteFields", note=obj)
        else:
            logger.warning(f"cannot find target with id {id}")



if __name__ == "__main__":
    run()