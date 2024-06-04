import logging
import time
import json
import random
from functools import wraps
from anki_connect import invoke as anki_invoke
from tqdm import tqdm

from main import get_note_fields
from ai.gemini import rate

logger = logging.getLogger(__name__)


def validate(result, len_buffer):
    if not isinstance(result, list):
        raise Exception("ai response is not a valid list")

    if len(result) != len_buffer:
        raise Exception("ai response len doesn't match")

    for item in result:
        if "score" not in item or "culture" not in item or "reason" not in item:
            raise Exception("missing field in ai response item")

    return True


def get_frequency_tag(score):
    try:
        score_int = int(score)
        if score_int >= 80:
            return "K_daily"
        if score_int >= 60:
            return "K_usual"
        if score_int >= 40:
            return "K_occasional"
        if score_int >= 20:
            return "K_infrequent"
        else:
            return "K_rare"
    except Exception as e:
        logger.error(f"Unknown score {score}")


def get_category_tag(culture):
    if not isinstance(culture, str):
        return []
    if "," in culture:
        splited = culture.split(",")
        return [element.strip() for element in splited]
    return [culture]


def retry(max_retries, delay=1):
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    print(f"Attempt {retries} failed: {e}")
                    time.sleep(delay)
                    last_error = e
            raise Exception(last_error)

        return wrapper

    return decorator_retry


@retry(max_retries=5, delay=1)
def try_to_get_valid_response(questions, len_buffer):
    try:
        resp = rate(questions)
        text = resp.text
        result = json.loads(text)
        validate(result, len_buffer)
        return None, result
    except Exception as e:
        return e, None


def tag_score(buffer):
    questions = [(word, definition) for _, word, definition in buffer]

    err, result = try_to_get_valid_response(questions, len(buffer))

    if err:
        logger.error(err)
        logger.debug(f"err question content:")
        for nid, word, definition in buffer:
            logger.debug(f'{nid}. "{word}": {definition}')
        return False

    for idx, item in enumerate(result):
        f_tag = get_frequency_tag(item["score"])
        c_tag = get_category_tag(item["culture"])
        brief = item["reason"]
        anki_invoke(
            "updateNote",
            note={
                "id": buffer[idx][0],
                "fields": {"brief": brief},
                "tags": [f_tag, *c_tag],
            },
        )
        logger.info(f"note {buffer[idx][0]} successfully tagged.")

    return True


def remove_non_ascii(text):
    return text.encode("ascii", errors="ignore").decode()


def run():
    logging.basicConfig(
        filename="ai.log",
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )
    logger.info("Start ai")

    nids = anki_invoke("findNotes", query="deck:KEXP::Read tag:none")
    random.Random(123).shuffle(nids)

    # contains definition that is considered bad by ai
    blacklist = [1716005118535, 1716005118662]
    bad_words = [" sex ", " intercourse "]

    buffer = []
    for idx, nid in enumerate(tqdm(nids)):
        if nid in blacklist:
            continue

        if len(buffer) >= 16 or idx >= len(nids) - 1:
            logger.info("start tagging")
            result = tag_score(buffer)
            if not result:
                logger.warning(
                    "tagging failed for {}".format(
                        ", ".join([str(nid) for nid, _, _ in buffer])
                    )
                )
                break
            buffer.clear()
            logger.info("sleeping 4s")
            time.sleep(4)

        note = get_note_fields(nid)

        usage = note.get("usage", "")
        term = note.get("term", "")
        if usage:
            if "~" in usage:
                usage = usage.replace("~", term)
            elif "+" in usage:
                usage = usage.replace("+", f"{term} +")

        word = usage if usage else term
        word = remove_non_ascii(word)

        definition = note.get("definition", "")
        if not word or not definition:
            logger.warning(f"no term or definition for nid {nid}")
            continue

        for bad_word in bad_words:
            if bad_word in definition:
                logger.warning(f"note {nid} filtered")
                continue

        buffer.append((nid, word, definition))


if __name__ == "__main__":
    run()
    # test()
