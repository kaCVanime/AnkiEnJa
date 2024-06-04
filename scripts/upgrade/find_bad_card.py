import logging
from anki_connect import invoke as anki_invoke
from tqdm import tqdm
from main import (
    get_note_fields,
    get_note_ids_from_last,
    get_last_note_id,
    set_last_note_id,
)

logger = logging.getLogger(__name__)


def insert_at(string, index, target):
    return string[:index] + target + string[index:]


def term_in_usage(term, usage):
    separators = ["ˈ", "ˌ"]
    plural = ["s", "ies", "es"]
    ings = ["ing"]

    if term in usage:
        return True
    for p in plural:
        if (term[0:-1] + p) in usage:
            return True
    for ing in ings:
        if (term + ing) in usage:
            return True

    for i in range(1, len(term)):
        for sep in separators:
            variant = insert_at(term, i, sep)
            if variant in usage:
                return True

    return False


def correct():
    bad = [
        ("chimney sweep", "sweep"),
        ("bell pepper", "pepper"),
        ("blowlamp", "torch"),
        ("courtyard", "court"),
        ("talent scout", "scout"),
        ("faze", "phase"),
        ("mom", "mum"),
        ("snarl-up", "snarl"),
        ("bell-ringer", "ringer"),
        ("newsflash", "flash"),
        ("cogwheel", "cog"),
        ("wack", "whack"),
        ("steeplechase", "chase"),
        ("rocking chair", "rocker"),
        ("flippant", "flip"),
        ("golf course", "course"),
        ("feint", "faint"),
        ("oil well", "well"),
        ("marijuana", "pot"),
        ("sett", "set"),
        ("worktop", "counter"),
        ("bhang", "bang"),
        ("mother-of-pearl", "pearl"),
        ("flagstone", "stone"),
        ("indium", "in"),
    ]
    bad = [("indium", "in")]
    bad_special = ["reckon_9", "reckon_10", "tear_30", "tear_31", "route_5"]
    need_remove = ["line_57", "line_59"]
    batch_remove = ["indium"]

    for weird, origin in tqdm(bad):
        nids = anki_invoke(
            "findNotes",
            query=f'(deck:KEXP::Read OR deck:KEXP::Write) "term:{weird}" -usage:',
        )
        for nid in nids:
            note = get_note_fields(nid)
            normal_id = note["id"].replace(
                weird.replace(" ", "_"), origin.replace(" ", "_")
            )
            anki_invoke(
                "updateNoteFields",
                note={
                    "id": nid,
                    "fields": {
                        "id": normal_id,
                        "term": origin,
                        "examples": note["examples"].replace(note["id"], normal_id),
                    },
                },
            )


# print(term_in_usage('hail', 'ˈhail from…'))
def run():
    logging.basicConfig(
        filename="find_bad_card.log",
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )
    logger.info("Finding")
    read_nids = anki_invoke("findNotes", query=f"deck:KEXP::Read")
    for nid in tqdm(read_nids):
        note = get_note_fields(nid)
        if (
            note["usage"]
            and "~" not in note["usage"]
            and "+" not in note["usage"]
            and not term_in_usage(note["term"], note["usage"])
        ):
            logger.info(f"bad card {note['term']}; {note['usage']}")


if __name__ == "__main__":
    # run()
    correct()
