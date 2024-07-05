import tqdm
import time
from loguru import logger
from pathlib import Path
from tqdm.contrib.concurrent import thread_map

from src.utils import DictHelper, import_from
from src.utils import Recorder
from src.dict_parser import ParserManager

log_path = Path('./src/logs')
temp_path = Path('./src/temp')
for p in (log_path, temp_path):
    p.mkdir(exist_ok=True)

logger.remove()
logger.add(log_path / 'main.log', level="INFO")

dict_helper = DictHelper()
parser = ParserManager()

results_recorder = Recorder()
results_recorder.start()



def is_redirect_entry(html):
    if html.startswith("@@@LINK="):
        return True
    return ParserManager.is_redirect_entry(html)

def get_redirect_word(html):
    # ParserManager = import_from("upgrade_ja.dict_parser.manager", "ParserManager")

    html = html.strip()
    LINK_KEYWORD = "@@@LINK="
    if html.upper().startswith(LINK_KEYWORD):
        redirect_word = html[len(LINK_KEYWORD):]
        if LINK_KEYWORD in redirect_word:
            raise NotImplementedError
        return redirect_word
    elif is_redirect_entry(html):
        return ParserManager.get_best_redirect_word(html)

    return html

def pick(html_results, word):
    if len(html_results) > 1:
        logger.warning('{}: multiple html results found', word)

    if not is_redirect_entry(html_results[0]):
        return html_results[0]
    else:
        logger.warning('{} is a redirect word. skipping', word)
        return None
        # redirect = get_redirect_word(html_results[0])
        # html_results = dict_helper.query_oaldpe(redirect)
        # html = html_results[0]

def normalize(s):
    return s.replace('·', '')

@logger.catch
def main():
    with open('src/assets/COCA_20000.txt', mode='r', encoding='utf-8') as f:
        word_list = [r.strip() for r in f.readlines()]
    blacklist = ['republican', 'follow-up', 'em', 'start-up', 'trade-off', 'cut-off', 'close-up', 'warm-up', 'cover-up', 'stand-up', 'run-down', 'drop-off', 'run-up', 'Labour', 'break-in', 'sit-up', 'carry-on', 'stand-in', 'run-in', 'shake-up', 'blow-up']
    completed = [normalize(k) for k in results_recorder.get_keys()]
    todo = [w for w in word_list if w not in completed and w not in blacklist]

    thread_map(lookup, todo)


def lookup(word):
    html_results = dict_helper.query_oaldpe(word)
    if not html_results:
        html_results = dict_helper.query_oaldpe(word.lower())
    if not html_results:
        logger.error('no entry for {}', word)
        results_recorder.save_word_entry_only(word)
        return []

    html = pick(html_results, word)
    if not html:
        results_recorder.save_word_entry_only(word)
        return []

    results = parser.parse(html, word)

    if not results:
        logger.error('no results for {}', word)
        results_recorder.save_word_entry_only(word)
        return []

    t0 = time.perf_counter()
    results_recorder.save(results)
    t1 = time.perf_counter()
    logger.info('{} saved in {}s', word, t1-t0)

    return results

def test(word):
    return lookup(word)

if __name__ == '__main__':
    main()


    # results = test("tear")
    # def_ids = []
    # for r in results:
    #     for p in r["defs"]:
    #         assert p["id"] not in def_ids
    #         def_ids.append(p["id"])
    results_recorder.close()
    pass
