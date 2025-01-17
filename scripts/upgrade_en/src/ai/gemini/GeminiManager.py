from pathlib import Path
from loguru import logger
from queue import Queue
from threading import Lock, Thread
from tqdm.contrib.concurrent import thread_map
from itertools import tee, chain
from tqdm import tqdm
import random
import json
from functools import reduce

from .tasker import RateTasker, TranslateTasker, SenseTasker, ClassifyTasker, DefTranslateTasker, SynonymSenseTasker
from ..utils import Recorder


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

        self.synonym_sense_tasker = SynonymSenseTasker(self)
        self.synonym_sense_thread = Thread(target=self.synonym_sense_tasker.run, daemon=True)

        self.taskers = [self.rate_tasker, self.classify_tasker, self.translate_tasker, self.sense_tasker, self.def_translate_tasker, self.synonym_sense_tasker]
        self.threads = [self.rate_thread, self.classify_thread, self.translate_thread, self.sense_thread, self.def_translate_thread, self.synonym_sense_thread]

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
        elif tasker_type == SynonymSenseTasker:
            if result.get("dict_type", "") == 'Synonyms':
                result_recorder.update_synonyms_defs(result["id"], result["defs"])
            else:
                result_recorder.update_whichword_defs(result["id"], result["defs"])

        with logger.contextualize(
                **{
                    "update_db_type": tasker_type.__name__,
                    "topic": result.get("topic", "-"),
                    "score": result.get("score", "-"),
                    "reason": result.get("reason", "-"),
                    "examples": json.dumps(egs, ensure_ascii=False, indent=4) if (
                            egs := result.get("examples", "")) else '-',
                    "def_cn": result.get("def_cn", "-"),
                    "id": result["id"]
                }):
            logger.debug("{} updating db", tasker_type.__name__)

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

    # @logger.catch
    def _get_handlers(self, entry):
        handlers = []

        if (dict_type := entry.get("dict_type", "")) == 'Synonyms' or dict_type == 'Whichwords':
            pass
            if dict_type == 'Synonyms':
                processed = all([len(t["examples"]) >= 3 for t in entry["defs"]])
            else:
                processed = all([not isinstance(t, list) for t in entry["defs"]])

            if not processed:
                handlers.append(lambda e: self.handle_job(self.synonym_sense_tasker, e, priority=10))
            return handlers

        if not entry["topic"]:
            handlers.append(lambda e: self.handle_job(self.classify_tasker, e, priority=1))

        if not entry["reason"] and not entry["score"]:
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
        if (dict_type := entry.get("dict_type", "")) != 'Synonyms' and dict_type != 'Whichwords':
            entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []
            if not self._is_safe(entry["definition"]) or not self._is_safe(entry.get("word", "")) or not self._is_safe(entry.get("usage", "")):
                return
        else:
            entry["defs"] = json.loads(entry["defs"]) if entry["defs"] else []

        handlers = self._get_handlers(entry)
        for h in handlers:
            h(entry)
