import json

from loguru import logger
from pathlib import Path
from tqdm.contrib.concurrent import thread_map

from src.utils import Recorder, lookup
from src.dict_parser import ParserManager
from src.ai.manager import Manager as AIManager

log_path = Path('./src/logs')
temp_path = Path('./src/temp')
for p in (log_path, temp_path):
    p.mkdir(exist_ok=True)



log_result_ai_template = '''
{time} | {extra[id]} updated. ----------------------
{extra[update_db_type]}
{extra[topic]}
def_cn: {extra[def_cn]}
Score: {extra[score]}
Reason: {extra[reason]}
Examples:
{extra[examples]}
'''


logger.remove()
logger.add(log_path / 'main.log', level="INFO", filter=lambda r: 'src.ai' not in r['name'])
logger.add(log_path / 'ai.log', filter='src.ai', level="INFO")
logger.add(log_path / 'results.log', filter=lambda r: "update_db_type" in r["extra"], format=log_result_ai_template)


parser = ParserManager()

results_recorder = Recorder()


def normalize(s):
    return s.replace('·', '')

def get_coca():
    with open('src/assets/COCA_20000.txt', mode='r', encoding='utf-8') as f:
        word_list = [r.strip() for r in f.readlines()]
    return word_list


def get_todos(word_list):
    b1 = ['republican', 'follow-up', 'em', 'start-up', 'trade-off', 'cut-off', 'close-up', 'warm-up', 'cover-up', 'stand-up', 'run-down', 'drop-off', 'run-up', 'Labour', 'break-in', 'sit-up', 'carry-on', 'stand-in', 'run-in', 'shake-up', 'blow-up', 'layoff']
    b2 = ['tear', 'Bible', 'OK', 'makeup', 'Olympics', 'setup', 'cleanup', 'lineup', 'northwestern', 'fund-raiser', 'Freeman', 'runoff', 'payoff', 'breakup', 'best-seller', 'kinda', 'Pentagon', 'wake-up', 'kickoff', 'take-out', 'time-out', 'goddamned', 'roundup', 'side-by-side', 'telecom', 'hangout', 'reverend', 'holdout', 'e-mailed', 'on-the-job']
    blacklist=[*b1, *b2]
    completed = [normalize(k) for k in results_recorder.get_keys()]
    todo = [w for w in word_list if w not in completed and w not in blacklist]
    return todo

@logger.catch
def main():
    word_list = get_coca()
    def f(todo):
        return lookup(todo, word_list, save=True)

    thread_map(f, get_todos(word_list))

if __name__ == '__main__':
    main()

    # ai_manager = AIManager()
    # ai_manager.run()

    pass
