import pandas
import pickle
import threading
import logging
from pathlib import Path

from tqdm.contrib.concurrent import thread_map
from dict_lookup import lookup, mdx_helper
from dict_parser import ParserManager

from utils import is_string_katakana

parser = ParserManager()


logger = logging.getLogger(__name__)

lock = threading.Lock()

progress_file = 'progress.pkl'


if Path(progress_file).is_file():
    with open(progress_file, 'rb') as f:
        completed_items = pickle.load(f)
else:
    completed_items = []


def save_progress():
    with open(progress_file, 'wb') as f:
        pickle.dump(completed_items, f)

def get_jev_list():
    jev = pandas.read_excel("./assets/JEV.xlsx", header=1, index_col=0)
    data = jev[["標準的な表記", "読み"]]
    d1 = data.drop_duplicates(subset=["標準的な表記", "読み"])
    return d1.to_numpy().tolist()

def get_fallback_accent(word, yomi, mode):
    html = lookup(word, yomi, mode)
    if html:
        result = parser.parse(html)
        if result and result["accent"]:
            return result["accent"]
    return None

def process(item):
    word, yomi = item

    html = lookup(word, yomi)
    if not html:
        return

    result = parser.parse(html)
    if result:
        if not result['defs']:
            logger.error(f"{word}-{result['dict_type']}: no defs found")
        if not result['word'] and not result['kanji']:
            logger.error(f"{word}: no word or kanji found")
        logger.info("{word} - {kanji}".format(word=result['word'], kanji=result['kanji']))

        if not is_string_katakana(word) and not result['accent']:
            if result['dict_type'] == 'DJS':
                result['accent'] = get_fallback_accent(word, yomi, mode='MOJI')
            elif result['dict_type'] == 'Moji':
                result['accent'] = get_fallback_accent(word, yomi, mode='DJS')
            elif result['dict_type'] == 'XSJ':
                accent = get_fallback_accent(word, yomi, mode='DJS')
                if not accent:
                    accent = get_fallback_accent(word, yomi, mode='MOJI')
                result['accent'] = accent

        if not is_string_katakana(word) and not result['accent']:
            logger.error(f"{word}: no accent found")
    else:
        logger.error(f"{word}: parse failed")


    with lock:
        completed_items.append(item)
        save_progress()


def run():
    logging.basicConfig(
        filename="upgrade.log",
        level=logging.ERROR,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
        encoding='utf-8'
    )

    jev_list = get_jev_list()
    todo = [item for item in jev_list if item not in completed_items]

    thread_map(process, todo)

    print(mdx_helper.xsj_count, mdx_helper.moji_count, mdx_helper.djs_count)





if __name__ == '__main__':
    run()