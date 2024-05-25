import logging
from anki_connect import invoke as anki_invoke
from tqdm import tqdm
from main import get_note_fields, get_note_ids_from_last, get_last_note_id, set_last_note_id

logger = logging.getLogger(__name__)

def normalize(tag):
    tag = tag.encode("ascii", errors="ignore").decode().strip()
    return f"L_{tag.replace(' ', '_')}"

def run():
    logging.basicConfig(
        filename="transform_label.log",
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )
    logger.info("Start transform")

    nids = anki_invoke("findNotes", query="deck:KEXP::Read label:re:.+")
    nids = get_note_ids_from_last(nids, get_last_note_id())

    for nid in tqdm(nids):
        note = get_note_fields(nid)

        label = note["label"].strip()
        if not label.startswith("("):
            logger.info(f"note {nid} passed. {label}")
            continue
        label = label[1:-1]
        raw_tags = label.split(",")
        tags = [normalize(tag) for tag in raw_tags]
        tag_str = " ".join(tags)

        anki_invoke("addTags", notes=[nid], tags=tag_str)
        logger.info(f"note {nid} transformed")

        set_last_note_id(nid)


if __name__ == "__main__":
    run()