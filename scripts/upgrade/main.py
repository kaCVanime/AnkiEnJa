# create one-definition-per-note deck from old deck

import logging
import json
from anki_connect import invoke as anki_invoke
from pathlib import Path
from tqdm import tqdm

from models.models import ModelListen, ModelRead, ModelWrite

logger = logging.getLogger(__name__)

new_deck_name = "KEXP"
filter_label = [
    "AustralE",
    "SAfrE",
    "NEngE",
    "IndE",
    "ScotE",
    "WAfrE",
    "WelshE",
    "IrishE",
    "specialist",
]


def create_decks(deck_name):
    names = [
        deck_name,
        f"{deck_name}::Read",
        f"{deck_name}::Write",
        f"{deck_name}::Listen",
    ]
    deck_names = anki_invoke("deckNames")
    for name in names:
        if name not in deck_names:
            anki_invoke("createDeck", deck=name)


def get_last_note_id():
    last_note_file = Path("last_note.txt")
    if last_note_file.is_file():
        with open(last_note_file, mode="r", encoding="utf-8") as f:
            return f.readline()
    return None


def set_last_note_id(id):
    last_note_file = Path("last_note.txt")
    with open(last_note_file, mode="w", encoding="utf-8") as f:
        f.write(str(id))
    return True


def get_note_ids_from_last(ids=None, id=None):
    if ids is None:
        ids = []
    if not id:
        return ids
    if id in ids:
        index = ids.index(id)
        return ids[index:]


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]


def get_note_fields(nid):
    note = get_note(nid)
    return {key: value_dict["value"] for key, value_dict in note["fields"].items()}


def has_filter_label(item):
    if not item.get("label"):
        return False
    return any(pattern in item["label"] for pattern in filter_label)


def parse_json(string):
    try:
        obj = json.loads(string)
        return obj
    except json.JSONDecodeError:
        return None


def convert_phrv_data(data):
    result = []
    for item in data:
        if isinstance(item.get("defs"), list):
            for definition in item["defs"]:
                updated_def = {
                    **definition,
                    "usage": definition.get("usage", item.get("usage")),
                }
                result.append(updated_def)
    return result


def get_new_note_fields(note, definition_item, definition_idx):
    c_note_fields = {
        "id": f'{note["term"].replace(" ", "_")}_{definition_idx}',
        "term": note.get("term"),
        "AmEPhonetic": note.get("AmEPhonetic", ""),
        "BrEPhonetic": note.get("BrEPhonetic", ""),
        "label": definition_item.get("label", note.get("label", "")),
        "usage": definition_item.get("usage", ""),
        "definition": definition_item.get("definition", ""),
        "def_cn": definition_item.get("def_cn", ""),
        "audio": ""
    }

    # if definition_item["definition"]:
    #     score, culture = ai_manager.rate(
    #         note["term"], definition_item["definition"]
    #     )
    #     if culture and culture not in c_note_fields["label"]:
    #         c_note_fields["label"] = c_note_fields["label"] + f"({culture})"
    #     c_note_tags.append(score)

    if definition_item.get("examples"):
        valid_eg_count = 0
        examples = []
        for eg in definition_item["examples"]:
            if has_filter_label(eg):
                continue

            eg_name = "{term}_{def_idx}_{eg_idx}".format(
                term=note["term"].replace(" ", "_"),
                def_idx=definition_idx,
                eg_idx=valid_eg_count,
            )
            valid_eg_count += 1
            examples.append({**eg, "name": eg_name})

        c_note_fields["examples"] = json.dumps(examples)

    return c_note_fields


def main():
    logging.basicConfig(
        filename="upgrade.log",
        level=logging.INFO,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )
    logger.info("Start")

    # try:
    create_decks(new_deck_name)

    read_model = ModelRead(new_deck_name)
    write_model = ModelWrite(new_deck_name)

    nids = anki_invoke("findNotes", query="deck:raw")
    nids = get_note_ids_from_last(nids, get_last_note_id())

    for nid in tqdm(nids):
        note = get_note_fields(nid)

        if has_filter_label(note):
            continue

        note_examples = parse_json(note["examplesJson"]) or []
        note_phrvs = convert_phrv_data(parse_json(note["phraseVerbsJson"]) or [])
        note_idioms = convert_phrv_data(parse_json(note["idiomsJson"]) or [])

        for definition_idx, definition_item in enumerate(
            [*note_examples, *note_phrvs, *note_idioms]
        ):
            if has_filter_label(definition_item):
                continue

            new_note_fields = get_new_note_fields(
                note, definition_item, definition_idx
            )

            read_model.add_note(new_note_fields)
            write_model.add_note(new_note_fields)

        logger.info(f'note {nid} added')
        set_last_note_id(nid)
    # except Exception as e:
    #     print(e)
        # logger.error(e, exc_info=True)

    logger.info("End")


if __name__ == "__main__":
    main()
