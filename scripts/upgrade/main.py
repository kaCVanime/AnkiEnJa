# create one-definition-per-note deck from old deck

import logging
import json
from anki_connect import invoke as anki_invoke
from pathlib import Path
from ai.manager import AIManager

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


def get_new_deck_id(deck_name):
    deck_dict = anki_invoke("deckNamesAndIds")
    if deck_name not in deck_dict:
        new_deck_id = anki_invoke("createDeck", deck=deck_name)
    else:
        new_deck_id = deck_dict[deck_name]
    return new_deck_id


def get_last_note_id():
    last_note_file = Path("last_note.txt")
    if last_note_file.is_file():
        with open(last_note_file, mode="r", encoding="utf-8") as f:
            return f.readline()
    return None


def set_last_note_id(id):
    last_note_file = Path("last_note.txt")
    with open(last_note_file, mode="w+", encoding="utf-8") as f:
        f.write(id)
    return True


def get_note_ids_from_last(ids=[], id=None):
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
    if not item["label"]:
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
        if isinstance(item.get('defs'), list):
            for definition in item['defs']:
                updated_def = {**definition, 'usage': definition.get('usage', item.get('usage'))}
                result.append(updated_def)
    return result

def main():
    logging.basicConfig(
        filename="upgrade.log",
        level=logging.INFO,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )
    logger.info("Start")
    logger.error("test")

    ai_manager = AIManager()

    new_deck_id = get_new_deck_id(new_deck_name)

    subdeck_id_read = get_new_deck_id(f"{new_deck_name}::read")
    subdeck_id_write = get_new_deck_id(f"{new_deck_name}::write")
    subdeck_id_listen = get_new_deck_id(f"{new_deck_name}::listen")

    nids = anki_invoke("findNotes", query="deck:raw")
    nids = get_note_ids_from_last(nids, get_last_note_id())

    for nid in nids:
        note = get_note_fields(nid)

        if has_filter_label(note):
            continue

        note_examples = parse_json(note["examplesJson"]) or []
        note_phrvs = convert_phrv_data(parse_json(note["phraseVerbsJson"]) or [])
        note_idioms = convert_phrv_data(parse_json(note["idiomsJson"]) or [])

        for definition_idx, definition_item in enumerate([*note_examples, *note_phrvs, *note_idioms]):
            if has_filter_label(definition_item):
                continue

            c_note_tags = []
            c_note_fields = {}
            c_note_fields["AmEPhonetic"] = note["AmEPhonetic"]
            c_note_fields["label"] = (
                definition_item["label"]
                if definition_item["label"]
                else (note["label"] or "")
            )
            c_note_fields["usage"] = (
                definition_item["usage"] if definition_item["usage"] else ""
            )
            c_note_fields["definition"] = (
                definition_item["definition"] if definition_item["definition"] else ""
            )
            c_note_fields["def_cn"] = (
                definition_item["def_cn"] if definition_item["def_cn"] else ""
            )

            if definition_item["definition"]:
                score, culture = ai_manager.rate(
                    note["term"], definition_item["definition"]
                )
                if culture and culture not in c_note_fields["label"]:
                    c_note_fields["label"] = c_note_fields["label"] + f"({culture})"
                c_note_tags.append(score)

            if definition_item["examples"]:
                valid_eg_count = 0
                examples = []
                for eg in definition_item["examples"]:
                    if has_filter_label(eg):
                        continue

                    valid_eg_count += 1
                    eg_name = "{term}_{def_idx}_{eg_idx}".format(
                        term=note["term"].replace(" ", "_"),
                        def_idx=definition_idx,
                        eg_idx=valid_eg_count,
                    )

                    examples.append(
                        {**eg, "name": eg_name}
                    )

                c_note_fields["examples"] = examples
