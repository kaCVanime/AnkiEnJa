import pandas
import pickle
import threading
from pathlib import Path
from itertools import chain

from tqdm.contrib.concurrent import thread_map
from tqdm import tqdm

from loguru import logger

from upgrade_ja.recorder import Recorder
from upgrade_ja.dict_lookup import lookup, mdx_helper
from upgrade_ja.dict_parser.manager import ParserManager
from upgrade_ja.dict_parser.guanyongju import CommonIdiomsIterator
from upgrade_ja.ai.manager import ResultIterator

from upgrade_ja.utils import is_string_katakana

logger.add('upgrade_ja.log')


parser = ParserManager()

lock = threading.Lock()

jev_progress_recorder = Recorder('progress.pkl')
jev_results_recorder = Recorder('jev_results.pkl')

common_idioms_dir = Path('./upgrade_ja/assets/idioms_corrected')



entry_has_idiom_count = 0
entry_has_phrase_count = 0
entry_has_idiom_and_phrase_count = 0
idiom_count = 0
phrase_count = 0


def get_jev_list():
    jev = pandas.read_excel("./upgrade_ja/assets/JEV.xlsx", header=1, index_col=0)
    data = jev[["標準的な表記", "読み"]]
    d1 = data.drop_duplicates(subset=["標準的な表記", "読み"])
    return d1.to_numpy().tolist()


def get_fallback_accent(word, yomi, mode):
    html = lookup(word, yomi, mode)
    if html:
        result = parser.parse(html, mode="accent")
        if result and result["accent"]:
            return result["accent"]
    return None


def try_fallback_accent(result, word, yomi):
    if result["dict_type"] == "DJS":
        return get_fallback_accent(word, yomi, mode="MOJI")
    elif result["dict_type"] == "Moji":
        return get_fallback_accent(word, yomi, mode="DJS")
    elif result["dict_type"] == "XSJ":
        accent = get_fallback_accent(word, yomi, mode="DJS")
        if not accent:
            return get_fallback_accent(word, yomi, mode="MOJI")

    return None


def process(item):
    global \
        idiom_count, \
        phrase_count, \
        entry_has_idiom_count, \
        entry_has_phrase_count, \
        entry_has_idiom_and_phrase_count
    word, yomi = item

    html = lookup(word, yomi)

    with lock:
        jev_progress_recorder.save(item)

    if not html:
        return

    result = parser.parse(html)
    if not result:
        return
    if not result["defs"] or (not result["word"] and not result["kanji"]):
        return
    if not is_string_katakana(word) and not result["accent"]:
        result["accent"] = try_fallback_accent(result, word, yomi)

    if result["idioms"]:
        entry_has_idiom_count += 1
        idiom_count += len(result["idioms"])
    if result["phrases"]:
        entry_has_phrase_count += 1
        phrase_count += len(result["phrases"])
    if result["idioms"] and result["phrases"]:
        entry_has_idiom_and_phrase_count += 1

    with lock:
        jev_results_recorder.save(result)

    return result

def enhance(result):
    pass

def run():
    global \
        idiom_count, \
        phrase_count, \
        entry_has_idiom_count, \
        entry_has_phrase_count, \
        entry_has_idiom_and_phrase_count

    logger.info('start running')
    logger.info('processing jev entries')
    logger.remove()
    logger.add('upgrade_ja.log')

    jev_list = get_jev_list()
    completed_items = jev_progress_recorder.get()
    todo = [item for item in jev_list if item not in completed_items]

    # thread_map(process, todos, max_workers=1)
    jev_todo_results = filter(None, thread_map(process, todo))
    jev_results = chain(jev_results_recorder.get(), jev_todo_results)

    logger.info('dict query count: XSJ: {xsj}; DJS: {djs}; Moji: {moji}.'.format(xsj=mdx_helper.xsj_count, djs=mdx_helper.djs_count, moji=mdx_helper.moji_count))
    logger.info(f"querying XSJ dict for idioms and phrases..")
    logger.info(f"Found {idiom_count} idioms, {phrase_count} phrases.")
    logger.info(
        f"There are {entry_has_idiom_count} entries has idiom.\n {entry_has_phrase_count} entries has phrases.\n {entry_has_idiom_and_phrase_count} entries has both idioms and phrases."
    )

    common_idioms_iter = iter(CommonIdiomsIterator(common_idioms_dir))
    logger.info('fetching AI enhanced results')
    # thread_map(enhance, ResultIterator(chain(jev_results, common_idioms_iter)))
    enhanced_results = iter(ResultIterator(chain(jev_results, common_idioms_iter)))
    for i in enhanced_results:
        logger.info(i)
        pass


if __name__ == "__main__":
    run()
