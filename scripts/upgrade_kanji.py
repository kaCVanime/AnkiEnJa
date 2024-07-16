import re
import sys
from tqdm import tqdm
from loguru import logger

from upgrade_ja.anki.anki_connect import invoke as anki_invoke
from upgrade_ja.dict_lookup import lookup
from upgrade_ja.dict_parser.manager import ParserManager
from upgrade_ja.utils import convert_to_hiragana

logger.remove()
# logger.add('abc.log', level='INFO')
logger.add('badabc.log', level='ERROR')

parser = ParserManager()


def get_note(nid):
    ids = anki_invoke("notesInfo", notes=[nid])
    return ids[0]


def get_note_fields(nid):
    note = get_note(nid)
    return {
        **{key: value_dict["value"] for key, value_dict in note["fields"].items()},
        "tags": note["tags"]
    }

def handle_word(w):
    return re.sub(r"[・‐]", "", w)
def handle_kanji(k):
    k = re.sub(r"[(（](.+?)[）)]", "", k)
    return k.split("・")[0]

@logger.catch
def process(nid):
    fields = get_note_fields(nid)
    if re.search(r'[a-zA-Z]', fields["kanji"]):
        return
    html = lookup(handle_kanji(fields["kanji"]), handle_word(fields["word"]), mode="DJS")
    if not html:
        return
    result = parser.parse(html)
    if result["dict_type"] != "DJS" or not result["kanji"]:
        return

    kanji = result["kanji"].strip()
    if kanji.startswith("【") and kanji.endswith("】"):
        kanji = kanji[1:-1]
    if kanji == fields["kanji"]:
        return
    nids = anki_invoke("findNotes", query=f"deck:KJXP id:{fields['id']}")
    for nid in nids:
        note = {
            "id": nid,
            "fields": {
                "kanji": kanji
            }
        }
        anki_invoke("updateNoteFields", note=note)
    logger.info("{}: {} -> {}".format(fields["id"], fields["kanji"], kanji))


def main():
    nids = anki_invoke("findNotes", query="deck:KJXP::Read -kanji:")

    for nid in tqdm(nids):
        process(nid)

def correct_for_idiom(nid):
    fields = get_note_fields(nid)
    if re.search(r'[a-zA-Z]', fields["kanji"]):
        return None
    word = re.sub(r'[・‐]', "", fields["word"])
    l_k = len(fields["kanji"])
    l_w = len(word)
    idiom = fields["id"]
    if l_k <= 3 and l_w >= 6 and "_" not in idiom and convert_to_hiragana(fields["kanji"]) != word:
        nids = anki_invoke("findNotes", query=f"deck:KJXP id:{idiom}")
        for nid in nids:
            note = {
                "id": nid,
                "fields": {
                    "kanji": idiom
                }
            }
            anki_invoke("updateNoteFields", note=note)
        logger.error("{} -> {}".format(fields["kanji"], idiom))


def test():
    nids = anki_invoke("findNotes", query="deck:KJXP::Read -kanji:")
    for nid in tqdm(nids):
        correct_for_idiom(nid)


if __name__ == '__main__':
    # main()
    test()