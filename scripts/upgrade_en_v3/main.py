from loguru import logger
from pathlib import Path
from tqdm.contrib.concurrent import thread_map

from src.utils import Recorder, lookup
from src.dict_parser import ParserManager

log_path = Path('./src/logs')
temp_path = Path('./src/temp')
for p in (log_path, temp_path):
    p.mkdir(exist_ok=True)

logger.remove()
logger.add(log_path / 'main.log', level="INFO")

parser = ParserManager()

results_recorder = Recorder()


def normalize(s):
    return s.replace('·', '')

def get_coca():
    with open('src/assets/COCA_20000.txt', mode='r', encoding='utf-8') as f:
        word_list = [r.strip() for r in f.readlines()]
    return word_list


def get_todos(word_list):
    blacklist = ['republican', 'follow-up', 'em', 'start-up', 'trade-off', 'cut-off', 'close-up', 'warm-up', 'cover-up', 'stand-up', 'run-down', 'drop-off', 'run-up', 'Labour', 'break-in', 'sit-up', 'carry-on', 'stand-in', 'run-in', 'shake-up', 'blow-up']
    completed = [normalize(k) for k in results_recorder.get_keys()]
    todo = [w for w in word_list if w not in completed and w not in blacklist]
    return todo

@logger.catch
def main():
    word_list = get_coca()
    def f(todo):
        return lookup(todo, word_list)

    thread_map(f, get_todos(word_list))



def test(word):
    word_list = get_coca()
    return lookup(word, word_list)

if __name__ == '__main__':
    results_recorder.start()
    # main()


    results = test("Thermos")
    # def_ids = []
    # for r in results:
    #     for p in r["defs"]:
    #         assert p["id"] not in def_ids
    #         def_ids.append(p["id"])
    results_recorder.close()
    pass
