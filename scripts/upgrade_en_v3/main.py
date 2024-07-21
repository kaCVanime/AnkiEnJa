import tqdm
from loguru import logger
from pathlib import Path
from tqdm.contrib.concurrent import thread_map

from src.utils import Recorder, DictHelper, import_from
from src.dict_parser import ParserManager

log_path = Path('./src/logs')
temp_path = Path('./src/temp')
for p in (log_path, temp_path):
    p.mkdir(exist_ok=True)

logger.remove()
logger.add(log_path / 'main.log', level="WARNING")

dict_helper = DictHelper()
parser = ParserManager()

coca_progress_recorder = Recorder(temp_path / 'coca_progress.pkl')
coca_results_recorder = Recorder(temp_path / 'coca_results.pkl')



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


@logger.catch
def main():
    with open('src/assets/COCA_20000.txt', mode='r', encoding='utf-8') as f:
        word_list = [r.strip() for r in f.readlines()]

    completed = coca_progress_recorder.get()
    todo = [w for w in word_list if w not in completed]

    thread_map(lookup, todo)



def lookup(word):
    html_results = dict_helper.query_oaldpe(word)
    if not html_results:
        html_results = dict_helper.query_oaldpe(word.lower())
    if not html_results:
        logger.error('no entry for {}', word)
        return []

    html = pick(html_results, word)
    if not html:
        return []

    results = parser.parse(html, word)

    if not results:
        logger.error('no results for {}', word)

    coca_progress_recorder.save(word)
    coca_results_recorder.save(results)

    return results

def test(word):
    return lookup(word)

if __name__ == '__main__':
    # main()
    results = test("take")
    pass
