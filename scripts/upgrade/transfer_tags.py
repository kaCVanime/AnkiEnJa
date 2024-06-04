import logging

from anki_connect import invoke as anki_invoke
from tqdm import tqdm

from main import get_note_fields

logger = logging.getLogger(__name__)


def run():
    src_nids = anki_invoke("findNotes", query="deck:KEXP::Read -tag:none")
    for nid in tqdm(src_nids):
        note = get_note_fields(nid)
        tags = anki_invoke("getNoteTags", note=nid)
        target_nids = anki_invoke(
            "findNotes", query=f"deck:KEXP::Write id:{note['id']}"
        )
        if len(target_nids):
            anki_invoke("addTags", notes=target_nids, tags=" ".join(tags))


e

if __name__ == "__main__":
    run()
