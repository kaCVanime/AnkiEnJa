import json
from copy import deepcopy
from tqdm import tqdm
from itertools import tee
import sys

print(__name__)

from ...utils import Recorder
from .batcher import TranslateBatcher, SenseBatcher, RateBatcher



result_recorder = Recorder()

translator = TranslateBatcher()
sensor = SenseBatcher()
rater = RateBatcher()


def get_taskers(entry):
    taskers = []

    if any([eg.get("ai", False) for eg in entry["examples"]]):
        taskers.append(translator)

    # if not entry["f_sense"] and not entry["f_word"] and not (entry["cefr"] == 'A1' or entry["cefr"] == 'A2'):
    #     taskers.append(rater)

    # if (entry["cefr"] != 'A1' and entry["cefr"] != 'A2') and (entry["f_sense"] != 'Low' and entry["f_word"] != 'Low') and len(entry['examples']) <= 3 :
    #     taskers.append(sensor)

    return taskers

def process(entry):
    entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []

    taskers = get_taskers(entry)
    for ts in taskers:
        e = ts.preprocess_entries([deepcopy(entry)])
        ts.adjust_instruction(e)
        ts.handle(f'{entry["id"]}-{ts.name}', ts.current_instruction, ts.construct_question(e))


def main():
    todos = result_recorder.get_todos()
    todos, todos_clone = tee(todos)
    for todo in tqdm(todos, total=len(list(todos_clone))):
        process(todo)


if __name__ == '__main__':
    main()