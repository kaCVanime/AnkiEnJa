from loguru import logger
import time


from ..dict_parser import ParserManager
from . import DictHelper, Recorder

dict_helper = DictHelper()
results_recorder = Recorder()
parser = ParserManager()


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
    logger.debug('{} saved in {}s', word, t1-t0)

    return results

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