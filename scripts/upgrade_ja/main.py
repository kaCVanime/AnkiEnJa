import pandas
import pickle
import threading
import logging
import re
from pathlib import Path

from tqdm import tqdm
from mdict_query.mdict_query import IndexBuilder
from tqdm.contrib.concurrent import thread_map
import jaconv

from dict_helper import DictHelper
mdx_helper = DictHelper()

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
    jev = pandas.read_excel("JEV.xlsx", header=1, index_col=0)
    data = jev[["標準的な表記", "読み"]]
    d1 = data.drop_duplicates(subset=["標準的な表記", "読み"])
    return d1.to_numpy().tolist()

def is_katakana(text):
    return all("\u30A0" <= c <= "\u30FF" for c in text)

def redirect_if_link(result, word, yomi):
    result = result.strip()
    LINK_KEYWORD = "@@@LINK="
    if result.upper().startswith(LINK_KEYWORD):
        redirect_word = result[len(LINK_KEYWORD):]
        if LINK_KEYWORD in redirect_word:
            logger.warning(f"{word}: Multiple LINK detected: {result}. Choosing 1st")
            redirect_word = redirect_word.split(LINK_KEYWORD)[0]
        results = builder.mdx_lookup(redirect_word)
        return pick(redirect_word, yomi, results)
    return result

def pick(word, yomi, results):
    if not len(results):
        results = mdx_helper.query_djs(word)
        if not len(results):
            logger.error(f'{word}-{yomi}. no entries')
            return None

    if len(results) > 1:
        logger.warning(f'{word} has multiple entries.')

    if not results[0].startswith('@@@LINK='):
        return results[0].strip()

    if is_katakana(word) or len(results) == 1:
        result = redirect_if_link(results[0], word, yomi)
    else:
        targets = list(filter(lambda res: f'{word}【{kata2hira(yomi)}】' in res or f'{kata2hira(yomi)}【{word}】' in res, results))
        if not len(targets):
            targets = mdx_helper.query_djs(word)
            if not len(targets):
                logger.error(f'{word}-{yomi}. no valid entries')
                return None
        if len(targets) > 1:
            logger.warning(f'{word} has multiple entries. choose the first one')
        result = redirect_if_link(targets[0], word, yomi)

    if not result:
        logger.error(f'{word}-{yomi}. no entries found')

    return result




def process(item):
    word, yomi = item
    # 全角英文转半角
    word = jaconv.z2h(word, kana=False, ascii=True, digit=True)

    results = mdx_helper.query_xsj(word)
    result = pick(word, yomi, results)
    # if not result:
    #     result = pick(word, yomi, )


    with lock:
        completed_items.append(item)
        save_progress()


def run():
    logging.basicConfig(
        filename="upgradeJA.log",
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
    )

    jev_list = get_jev_list()
    todo = [item for item in jev_list if item not in completed_items]

    thread_map(process, todo, max_workers=10)





if __name__ == '__main__':
    run()