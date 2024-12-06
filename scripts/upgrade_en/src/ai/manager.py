from loguru import logger
from threading import Lock, Thread
from tqdm.contrib.concurrent import thread_map
from itertools import tee, chain
from tqdm import tqdm
import json
from functools import reduce

from ..utils import Recorder

from .qwen.manager import QwenManager


result_recorder = Recorder()

lock = Lock()



class Manager:
    def __init__(self):
        self.result_recorder = result_recorder
        self.todos = chain(
            result_recorder.get_todos(),
            [
                {
                    **r,
                    "dict_type": "Synonyms"
                } for r in
                result_recorder.get_synonyms()
            ],
            [
                {
                    **r,
                    "dict_type": "Whichwords"
                } for r in
                result_recorder.get_whichwords()
            ]
        )

        self.blacklist = []

        self._manager = QwenManager(self)

        self.query_tqdm = None


    def _start(self):
        self._manager.start()
        logger.info('all tasker is prepared')

    def _finish(self):
        self._manager.finish()

        logger.info('all tasker terminated')
        self.query_tqdm.close()


    def update_progress(self, n):
        if self.query_tqdm:
            self.query_tqdm.update(n)

    def _init_query_tqdm(self):
        if self.query_tqdm:
            return

        self.query_tqdm = tqdm(total=self._manager.get_todo_size())

    def run(self):
        logger.info('start running')
        self._start()

        todos, todos_clone = tee(self.todos)

        print('adding todos')
        thread_map(self._process, todos, total=len(list(todos_clone)))

        print('fetching results from AI')
        self._init_query_tqdm()

        self._finish()

    # @logger.catch
    def _get_handlers(self, entry):
        return self._manager.get_handlers(entry)

    def _is_safe(self, item):
        if not item:
            return True
        for keyword in self.blacklist:
            if keyword in item:
                return False
        return True

    def _process(self, entry):
        if (dict_type := entry.get("dict_type", "")) != 'Synonyms' and dict_type != 'Whichwords':
            entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []
            if not self._is_safe(entry["definition"]) or not self._is_safe(entry.get("word", "")) or not self._is_safe(entry.get("usage", "")):
                return
        else:
            entry["defs"] = json.loads(entry["defs"]) if entry["defs"] else []

        handlers = self._get_handlers(entry)
        for h in handlers:
            h(entry)
