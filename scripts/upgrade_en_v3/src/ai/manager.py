from pathlib import Path
from loguru import logger
from queue import Queue
from threading import Lock, Thread
from tqdm.contrib.concurrent import thread_map
from itertools import tee
from tqdm import tqdm
import random
import json
from functools import reduce

from .tasker import RateTasker, TranslateTasker, SenseTasker, ClassifyTasker, DefTranslateTasker
from ..utils import Recorder


result_recorder = Recorder()

lock = Lock()



class Manager:
    def __init__(self, r):
        self.result_recorder = result_recorder
        self.todos = result_recorder.get_todos()

        self.blacklist = []

        self.rate_tasker = RateTasker(self)
        self.rate_thread = Thread(target=self.rate_tasker.run, daemon=True)

        self.classify_tasker = ClassifyTasker(self)
        self.classify_thread = Thread(target=self.classify_tasker.run, daemon=True)

        self.translate_tasker = TranslateTasker(self)
        self.translate_thread = Thread(target=self.translate_tasker.run, daemon=True)

        self.sense_tasker = SenseTasker(self)
        self.sense_thread = Thread(target=self.sense_tasker.run, daemon=True)

        self.def_translate_tasker = DefTranslateTasker(self)
        self.def_translate_thread = Thread(target=self.def_translate_tasker.run, daemon=True)

        self.taskers = [self.rate_tasker, self.classify_tasker, self.translate_tasker, self.sense_tasker, self.def_translate_tasker]
        self.threads = [self.rate_thread, self.classify_thread, self.translate_thread, self.sense_thread, self.def_translate_thread]

        self.query_tqdm = None


    def start_thread(self):
        for t in self.threads:
            t.start()
        logger.info('all tasker is prepared')

    def finish(self):
        for t in self.threads:
            t.join()

        logger.info('all tasker terminated')
        self.query_tqdm.close()

    def _update_db(self, tasker_type, result):
        if tasker_type == ClassifyTasker:
            result_recorder.update_def_topic(result["id"], result["topic"])
        elif tasker_type == RateTasker:
            result_recorder.update_def_rate(result["id"], result["score"], result["reason"])
        elif tasker_type == TranslateTasker or tasker_type == SenseTasker:
            result_recorder.update_def_examples(result["id"], json.dumps(result["examples"], ensure_ascii=False))
        elif tasker_type == DefTranslateTasker:
            result_recorder.update_def_cn(result["id"], result["def_cn"])

    @logger.catch
    def _handle_result(self, tasker_type, result):
        self._update_db(tasker_type, result)

    def handle_response(self, tasker_type, results):
        if results:
            if self.query_tqdm:
                self.query_tqdm.update(1)
            for result in results:
                self._handle_result(tasker_type, result)

    def _init_query_tqdm(self):
        if self.query_tqdm:
            return

        try:
            for t in self.taskers:
                t.porter_thread.join()
        except RuntimeError:
            pass
        todo_size = reduce(lambda total, tb: total + tb.get_queue_size(), self.taskers, 0)
        self.query_tqdm = tqdm(total=todo_size)

    def run(self):
        logger.info('start running')
        self.start_thread()

        todos, todos_clone = tee(self.todos)

        print('adding todos')
        thread_map(self.process, todos, total=len(list(todos_clone)))

        for t in self.taskers:
            if not t.is_start():
                t.force_start()

        print('fetching results from AI')
        self._init_query_tqdm()

        self.finish()


    def handle_job(self, tasker, entry, priority):
        tasker.append(entry, priority=priority)

    @logger.catch
    def _get_handlers(self, entry):
        handlers = []

        if not entry["topic"]:
            handlers.append(lambda e: self.handle_job(self.classify_tasker, e, priority=1))

        if not entry["reason"] or not entry["score"]:
            handlers.append(lambda e: self.handle_job(self.rate_tasker, e, priority=5))

        if not entry["def_cn"]:
            handlers.append(lambda e: self.handle_job(self.def_translate_tasker, e, priority=1))

        if any([eg["ai"] for eg in entry["examples"] if not eg.get("en_ai", False)]):
            handlers.append(lambda e: self.handle_job(self.translate_tasker, e, priority=10))

        if len(entry['examples']) < 3:
            handlers.append(lambda e: self.handle_job(self.sense_tasker, e, priority=100))

        return handlers

    def _is_safe(self, item):
        if not item:
            return True
        for keyword in self.blacklist:
            if keyword in item:
                return False
        return True

    def process(self, entry):
        entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []
        if not self._is_safe(entry["definition"]) or not self._is_safe(entry.get("word", "")) or not self._is_safe(entry.get("usage", "")):
            return
        handlers = self._get_handlers(entry)
        for h in handlers:
            h(entry)
