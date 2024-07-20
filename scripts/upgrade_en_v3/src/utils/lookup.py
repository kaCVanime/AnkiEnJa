from loguru import logger
import time
import re


from ..dict_parser import ParserManager
from . import DictHelper, Recorder

dict_helper = DictHelper()
results_recorder = Recorder()
parser = ParserManager()


def try_save(flag, word, results=None):
    if not flag:
        return

    if not results:
        results_recorder.save_word_entry_only(word)
        return

    t0 = time.perf_counter()
    results_recorder.save(results)
    t1 = time.perf_counter()
    logger.debug('{} saved in {}s', word, t1 - t0)


def lookup(word, word_list, save=True):
    html_results = dict_helper.query_oaldpe(word)
    if not html_results:
        html_results = dict_helper.query_oaldpe(word.lower())
    if not html_results:
        logger.error('no entry for {}', word)
        try_save(flag=save, word=word, results=None)
        return []

    html, redirect_word = pick(html_results, word, word_list, redirect_word=None)
    if not html:
        try_save(flag=save, word=word, results=None)
        return []

    results = parser.parse(html, word, redirect_word=redirect_word)

    if not results:
        logger.error('no results for {}', word)
        try_save(flag=save, word=word, results=None)
        return []

    try_save(flag=save, word=word, results=results)

    return results

@logger.catch
def pick(html_results, word, word_list, redirect_word=None):
    if len(html_results) > 1:
        logger.warning('{}: multiple html results found', word)

    if not is_redirect_entry(html_results[0]):
        return html_results[0], redirect_word
    else:
        redirect = re.sub('[_\d]', '', get_redirect_word(html_results[0]))
        if redirect and '|' not in redirect and redirect not in word_list:
            if word in word_list:
                word_list.remove(word)
            html_results = dict_helper.query_oaldpe(redirect)
            logger.warning('redirect {} to {}', word, redirect)
            return pick(html_results, word, word_list, redirect_word=redirect)

        logger.warning('{} is a redirect word. skipping', word)
        return None, None


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