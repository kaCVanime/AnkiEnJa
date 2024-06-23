from pathlib import Path

from tqdm import tqdm

from loguru import logger


from upgrade_ja.dict_parser.manager import ParserManager
from upgrade_ja.ai.manager import ResultIterator

from upgrade_ja.anki.manager import AnkiManager


log_path = Path('./upgrade_ja/logs')
temp_path = Path('./upgrade_ja/temp')
for p in (log_path, temp_path):
    p.mkdir(exist_ok=True)

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
logger.add(log_path / 'ai_rate_limiter.log', filter='upgrade_ja.ai.rate_limiter')
logger.add(log_path / 'ai.log', filter='upgrade_ja.ai')
# logger.add(log_path / 'ai.log', filter=lambda r: 'upgrade_ja.ai' in r['name'] and all([f'upgrade_ja.ai.{m}' not in r['name'] for m in ['manager', 'tasker', 'gemini', 'rate_limiter']]) )
logger.add(log_path / 'recorder.log', filter='upgrade_ja.recorder')
logger.add(log_path / 'dict_lookup.log', filter='upgrade_ja.dict_lookup')
logger.add(log_path / 'dict_parser_DJS.log', filter=filter_parser_log_by_dict_type('DJS'))
logger.add(log_path / 'dict_parser_MOJI.log', filter=filter_parser_log_by_dict_type('Moji'))
logger.add(log_path / 'dict_parser_XSJ.log', filter=filter_parser_log_by_dict_type('XSJ'))
logger.add(log_path / 'anki.log', filter='upgrade_ja.anki')

log_result_ai_template = '''
{time} | New result saved. ----------------------
{word}{kanji}
{categories}
Definition: {definition}
def_cn: {def_cn}
Score: {score}
Reason: {reason}
Examples:
{examples}
'''


def log_result_ai_formatter(record):
    ex = record["extra"]
    return log_result_ai_template.format(
        time=record["time"],
        word=ex["word"],
        kanji=ex["kanji"],
        definition=ex["definition"],
        def_cn=ex["def_cn"],
        score=ex["score"] if 'score' in ex else '',
        reason=ex["reason"] if 'reason' in ex else '',
        categories=ex["categories"] if 'categories' in ex else '',
        examples='\n'.join([f'{idx+1}. ja: {t["ja"]}\n cn: {t["cn"]}' for idx, t in enumerate(ex["examples"])])
    )


logger.add(log_path / 'result_ai.log', format=log_result_ai_formatter, filter=lambda r: 'upgrade_ja.recorder' in r['name'] and 'to ai' in r['message'] and 'ai_processing' not in r['message'])


parser = ParserManager()

def get_jlpt():
    from upgrade_ja.dict_helper import DictHelper
    mdx_helper = DictHelper()
    keys = mdx_helper.get_mdx_keys('JLPT')

    id_set = set()
    results = []

    for k in keys:
        rs = list(filter(lambda r: not r.strip().startswith('@@@LINK'), mdx_helper.query_jlpt(k)))
        if rs:
            d = parser.parse(rs[0])
            if "連用中止" in d["word"]:
                continue
            nid = d["word"] + d["defs"][0]["definition"]
            if nid not in id_set:
                id_set.add(nid)
                results.append(d)

    return results, filter(lambda r: "の違い" not in r["word"], results)



def run():
    print('start running')
    logger.info('start running')

    jlpt, for_ai = get_jlpt()

    print('fetching AI enhanced results')
    logger.info('fetching AI enhanced results')

    results = iter(ResultIterator(for_ai, force_stop=True))

    todos = list(filter(lambda r: r["dict_type"] == 'JLPT',  results))
    id_set = set()
    for item in todos:
        if item["id"] not in id_set:
            id_set.add(item["id"])
    for item in jlpt:
        definition = item['defs'][0]
        if definition["id"] not in id_set:
            id_set.add(definition["id"])
            todos.append({
                "dict_type": item["dict_type"],
                "word": item["word"],
                "usage": item["usage"],
                "kanji": item["kanji"],
                **definition
            })
    print(len(todos))

    anki_manager = AnkiManager('KJXP')

    for e in tqdm(todos):
        anki_manager.handle_jlpt(e)

if __name__ == "__main__":
    run()
