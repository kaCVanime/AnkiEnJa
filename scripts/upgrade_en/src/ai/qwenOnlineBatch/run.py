import json
from tqdm.contrib.concurrent import thread_map
import threading

lock = threading.Lock()

from ...utils import Recorder
from ..qwen.qwen import Translator, Senser

result_recorder = Recorder()

translator = Translator()
sensor = Senser()

def write_to_file_safe(filename, content):
    with lock:
        with open(filename, 'a') as f:
            f.write(content + '\n')

def get_taskers(entry):
    taskers = []

    if any([(eg.get("ai", False) and eg.get("tld", False)) for eg in entry["examples"]]):
        taskers.append(translator)

    if len(entry['examples']) <= 3:
        taskers.append(sensor)

def process(entry):
    entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []

    taskers = get_taskers(entry)


def main():
    todos = result_recorder.get_todos()


    pass




if __name__ == '__main__':
    main()