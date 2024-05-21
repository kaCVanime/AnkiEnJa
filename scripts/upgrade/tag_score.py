import logging
import time
import json
from anki_connect import invoke as anki_invoke
from tqdm import tqdm

from main import parse_json, get_note_fields, get_note_ids_from_last, get_last_note_id
from ai.gemini import rate

logger = logging.getLogger(__name__)

def is_valid(result, buffer):
    if not isinstance(result, list):
        logger.error("ai response is not a valid list")
        return False

    if len(result) != len(buffer):
        logger.error("ai response len doesn't match")
        return False

    for item in result:
        if "score" not in item or "culture" not in item or "reason" not in item:
            logger.error("missing field in ai response item {}", json.dumps(item))
            return False

    return True

def get_frequency_tag(score):
    try:
        score_int = int(score)
        if score_int >= 80:
            return 'K_daily'
        if score_int >= 60:
            return 'K_usual'
        if score_int >= 40:
            return 'K_occasional'
        if score_int >= 20:
            return 'K_infrequent'
        else:
            return 'K_rare'
    except Exception as e:
        logger.error(f"Unknown score {score}")

def get_category_tag(culture):
    if not isinstance(culture, str):
        return []
    if ',' in culture:
        splited = culture.split(',')
        return [element.strip() for element in splited]
    return [culture]

def tag_score(buffer):
    resp = rate([(word, definition) for _, word, definition in buffer])
    result = parse_json(resp.text)
    if not result:
        logger.error('Error in parsing resp {}'.format(resp.text))
        return False
    if not is_valid(result, buffer):
        return False

    for idx, item in enumerate(result):
        f_tag = get_frequency_tag(item["score"])
        c_tag = get_category_tag(item["culture"])
        brief = item["reason"]
        anki_invoke("updateNote", note={
            "id": buffer[idx][0],
            "fields": {
                "brief": brief
            },
            "tags": [f_tag, *c_tag]
        })
        logger.info(f"success for note {buffer[idx][0]}. continue")


    return True


def run():
    logging.basicConfig(
        filename="ai.log",
        level=logging.INFO,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )
    logger.info("Start ai")

    nids = anki_invoke("findNotes", query="deck:KEXP::Read")
    nids = get_note_ids_from_last(nids, get_last_note_id())

    buffer = []
    for nid in tqdm(nids):
        if len(buffer) >= 10:
            try:
                logger.info('start tagging')
                result = tag_score(buffer)
                if not result:
                    logger.warning('tagging failed for {}'.format(', '.join([str(nid) for nid, _, _ in buffer])))
                    break
                buffer.clear()
                logger.info('sleeping 4s')
                time.sleep(4)
            except Exception as e:
                logger.error(e)
                break

        note = get_note_fields(nid)

        usage = note.get("usage", "")
        term = note.get("term", "")
        if usage:
            usage = usage.replace("~", term)

        word = usage if usage else term
        definition = note.get("definition", "")
        if not word or not definition:
            logger.warning(f"no term or definition for nid {nid}")
            continue
        buffer.append((nid, word, definition))


if __name__ == "__main__":
    run()

