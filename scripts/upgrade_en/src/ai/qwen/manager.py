from loguru import logger
from threading import Lock, Thread

import json
from functools import reduce

from ...utils import Recorder

from .qwen import Translator, Senser
from ..tasker import Base as BaseTasker


result_recorder = Recorder()

lock = Lock()



class QwenManager:
    def __init__(self, parent):

        self.blacklist = []

        self.translate_tasker = TranslateTasker(self)
        self.translate_thread = Thread(target=self.translate_tasker.run, daemon=True)

        self.sense_tasker = SenseTasker(self)
        self.sense_thread = Thread(target=self.sense_tasker.run, daemon=True)

        self.taskers = [self.translate_tasker, self.sense_tasker]
        self.threads = [self.translate_thread, self.sense_thread]

        self._parent = parent


    def start(self):
        for t in self.threads:
            t.start()

    def finish(self):
        for t in self.threads:
            t.join()


    def _update_db(self, tasker_type, result):
        # if tasker_type == ClassifyTasker:
        #     result_recorder.update_def_topic(result["id"], result["topic"])
        # if tasker_type == RateTasker:
        #     result_recorder.update_def_rate(result["id"], result["score"], result["reason"])
        if tasker_type == TranslateTasker or tasker_type == SenseTasker:
            result_recorder.update_def_examples(result["id"], json.dumps(result["examples"], ensure_ascii=False))
        # elif tasker_type == SynonymSenseTasker:
        #     if result.get("dict_type", "") == 'Synonyms':
        #         result_recorder.update_synonyms_defs(result["id"], result["defs"])
        #     else:
        #         result_recorder.update_whichword_defs(result["id"], result["defs"])

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
            self._parent.update_progress(1)
            for result in results:
                self._handle_result(tasker_type, result)

    def get_todo_size(self):
        try:
            for t in self.taskers:
                t.porter_thread.join()
        except RuntimeError:
            pass
        return reduce(lambda total, tb: total + tb.get_queue_size(), self.taskers, 0)


    def _handle_job(self, tasker, entry, priority):
        tasker.append(entry, priority=priority)

    # @logger.catch
    def get_handlers(self, entry):
        handlers = []

        # if (dict_type := entry.get("dict_type", "")) == 'Synonyms' or dict_type == 'Whichwords':
        #     pass
        #     if dict_type == 'Synonyms':
        #         processed = all([len(t["examples"]) >= 3 for t in entry["defs"]])
        #     else:
        #         processed = all([not isinstance(t, list) for t in entry["defs"]])
        #
        #     if not processed:
        #         handlers.append(lambda e: self._handle_job(self.synonym_sense_tasker, e, priority=10))
        #     return handlers

        # if not entry["topic"]:
        #     handlers.append(lambda e: self._handle_job(self.classify_tasker, e, priority=1))
        #
        # if not entry["reason"] and not entry["score"]:
        #     handlers.append(lambda e: self._handle_job(self.rate_tasker, e, priority=5))

        # if any([(eg.get("ai", False) and eg.get("tld", False)) for eg in entry["examples"]]):
        #     handlers.append(lambda e: self._handle_job(self.translate_tasker, e, priority=10))

        if len(entry['examples']) <= 3:
            handlers.append(lambda e: self._handle_job(self.sense_tasker, e, priority=100))

        return handlers


class TranslateTasker(BaseTasker):
    capacity = 1
    def __init__(self, parent):
        super().__init__(parent, Translator())


class SenseTasker(BaseTasker):
    capacity = 1
    def __init__(self, parent):
        super().__init__(parent, Senser())


