import json
from tqdm.contrib.concurrent import thread_map
import sys


from ...utils import Recorder
from .batcher import TranslateBatcher, SenseBatcher, RateBatcher



result_recorder = Recorder()

translator = TranslateBatcher()
sensor = SenseBatcher()
rater = RateBatcher()


def get_taskers(entry):
    taskers = []

    # if any([(eg.get("ai", False) and eg.get("tld", False)) for eg in entry["examples"]]):
    #     taskers.append(translator)

    if not entry["reason"] and not entry["score"]:
        taskers.append(rater)

    if len(entry['examples']) <= 3:
        taskers.append(sensor)

    return taskers

def process(entry):
    entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []

    taskers = get_taskers(entry)
    for ts in taskers:
        e = ts.preprocess_entries([entry])
        ts.adjust_instruction(e)
        q = ts.construct_question(e)


def main():
    todos = result_recorder.get_todos()


    pass




if __name__ == '__main__':
    main()