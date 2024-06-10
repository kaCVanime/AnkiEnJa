import pandas
from pathlib import Path
from itertools import chain

from tqdm.contrib.concurrent import thread_map

from loguru import logger

from upgrade_ja.recorder import Recorder
from upgrade_ja.dict_lookup import lookup
from upgrade_ja.dict_parser.manager import ParserManager
from upgrade_ja.dict_parser.guanyongju import CommonIdiomsIterator
from upgrade_ja.ai.manager import ResultIterator

from upgrade_ja.utils import is_string_katakana

log_path = Path('./upgrade_ja/logs')
temp_path = Path('./upgrade_ja/temp')
for p in (log_path, temp_path):
    p.mkdir(exist_ok=True)

common_idioms_dir = Path('./upgrade_ja/assets/idioms_corrected_v2')


def filter_parser_log_by_dict_type(dict_type):
    def f(record):
        return "upgrade_ja.dict_parser" in record["name"] and record["extra"].get("dict_type", None) == dict_type
    return f

logger.remove()
logger.add(log_path / 'upgrade_ja.log', filter=lambda r: r['name'] == '__main__')
logger.add(log_path / 'ai_manager.log', filter='upgrade_ja.ai.manager')
logger.add(log_path / 'ai_tasker.log', filter='upgrade_ja.ai.tasker')
logger.add(log_path / 'ai_gemini.log', filter='upgrade_ja.ai.gemini')
logger.add(log_path / 'ai_retry.log', filter='upgrade_ja.ai.retry')
logger.add(log_path / 'ai.log', filter=lambda r: 'upgrade_ja.ai' in r['name'] and all([f'upgrade_ja.ai.{m}' not in r['name'] for m in ['manager', 'tasker', 'gemini']]) )
logger.add(log_path / 'recorder.log', filter='upgrade_ja.recorder')
logger.add(log_path / 'dict_lookup.log', filter='upgrade_ja.dict_lookup')
logger.add(log_path / 'dict_parser_DJS.log', filter=filter_parser_log_by_dict_type('DJS'))
logger.add(log_path / 'dict_parser_MOJI.log', filter=filter_parser_log_by_dict_type('Moji'))
logger.add(log_path / 'dict_parser_XSJ.log', filter=filter_parser_log_by_dict_type('XSJ'))
logger.add(log_path / 'rate_limiter.log', filter='upgrade_ja.ai.rate_limiter', level='INFO')


parser = ParserManager()

jev_progress_recorder = Recorder(temp_path / 'progress.pkl')
jev_results_recorder = Recorder(temp_path / 'jev_results.pkl')


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
        if accent:
            return accent
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
        if not result["accent"]:
            logger.warning(f"{word}-{yomi} no accent")

    if result["idioms"]:
        entry_has_idiom_count += 1
        idiom_count += len(result["idioms"])
    if result["phrases"]:
        entry_has_phrase_count += 1
        phrase_count += len(result["phrases"])
    if result["idioms"] and result["phrases"]:
        entry_has_idiom_and_phrase_count += 1

    jev_results_recorder.save(result)

    return result

def lookup_jev_entries():
    global \
        idiom_count, \
        phrase_count, \
        entry_has_idiom_count, \
        entry_has_phrase_count, \
        entry_has_idiom_and_phrase_count

    logger.info('processing jev entries')

    jev_list = get_jev_list()
    completed_items = jev_progress_recorder.get()
    todo = [item for item in jev_list if item not in completed_items]

    jev_todo_results = filter(None, thread_map(process, todo))
    return chain(jev_results_recorder.get(), jev_todo_results)

    # logger.info('dict query count: XSJ: {xsj}; DJS: {djs}; Moji: {moji}.'.format(xsj=mdx_helper.xsj_count, djs=mdx_helper.djs_count, moji=mdx_helper.moji_count))
    # logger.info(f"querying XSJ dict for idioms and phrases..")
    # logger.info(f"Found {idiom_count} idioms, {phrase_count} phrases.")
    # logger.info(
    #     f"There are {entry_has_idiom_count} entries has idiom.\n {entry_has_phrase_count} entries has phrases.\n {entry_has_idiom_and_phrase_count} entries has both idioms and phrases."
    # )


def enhance(result):
    pass


def run():
    print('start running')
    logger.info('start running')

    jev_results = lookup_jev_entries()

    common_idioms_iter = iter(CommonIdiomsIterator(common_idioms_dir))

    print('fetching AI enhanced results')
    logger.info('fetching AI enhanced results')
    # thread_map(enhance, ResultIterator(chain(jev_results, common_idioms_iter)))
    enhanced_jev_results = iter(ResultIterator(chain(jev_results, common_idioms_iter)))

    for i in enhanced_jev_results:
        pass


if __name__ == "__main__":
    run()
