from pathlib import Path
from loguru import logger
from queue import Queue
from threading import Lock, Thread
from tqdm.contrib.concurrent import thread_map
from itertools import tee
from tqdm import tqdm
import random

from .tasker import RateTasker, TranslateTasker, SenseTasker, ClassifyTasker, GrammarTranslateTasker, GrammarSenseTasker
from ..recorder import Recorder


result_recorder = Recorder(Path(__file__).parent.parent / 'temp' / 'ai.pkl')
processing_recorder = Recorder(Path(__file__).parent.parent / 'temp' / 'ai_processing.pkl')

lock = Lock()


class ResultIterator:
    def __init__(self, todos, force_stop=False):
        self.manager = Manager(todos)
        self.force_stop = force_stop
        if not force_stop:
            Thread(target=self.manager.run, daemon=True).start()

    def __iter__(self):
        self.items = iter(result_recorder.get())
        return self

    def __next__(self):
        try:
            return next(self.items)
        except StopIteration:
            if self.force_stop:
                raise StopIteration
            result = self.manager.consume()
            logger.debug('result retrieved. {}', result)
            if not result:
                logger.info('iteration stopped.')
                raise StopIteration
            return result


class Manager:
    def __init__(self, todos):
        self.todos = self._resume(todos)
        self.unfinished = {k["id"]: k for k in processing_recorder.get()}
        self.len_unfinished = len(self.unfinished.keys())
        logger.info('found {} unfinished items', self.len_unfinished)
        self.blacklist=["縊死い", "つ（吊）れる", "すっぽり", "【×吊る┊釣る】", "〜とき", "〜とあれば"]

        self.pool = Queue()

        self.rate_tasker = RateTasker(self)
        self.rate_thread = Thread(target=self.rate_tasker.run, daemon=True)

        self.classify_tasker = ClassifyTasker(self)
        self.classify_thread = Thread(target=self.classify_tasker.run, daemon=True)

        self.translate_tasker = TranslateTasker(self)
        self.translate_thread = Thread(target=self.translate_tasker.run, daemon=True)

        self.sense_tasker = SenseTasker(self)
        self.sense_thread = Thread(target=self.sense_tasker.run, daemon=True)

        self.grammar_translate_tasker = GrammarTranslateTasker(self)
        self.grammar_translate_thread = Thread(target=self.grammar_translate_tasker.run, daemon=True)

        self.grammar_sense_tasker = GrammarSenseTasker(self)
        self.grammar_sense_thread = Thread(target=self.grammar_sense_tasker.run, daemon=True)

        self.rate_status = {}
        self.translate_status = {}
        self.sense_status = {}
        self.classify_status = {}
        self.grammar_translate_status = {}
        self.grammar_sense_status = {}

        self.temp = {}

        self.query_tqdm = None


    def _resume(self, entries):
        already_done = [t["id"] for t in result_recorder.get()]
        todos = []
        for entry in entries:
            if "id" in entry and entry["id"] in already_done:
                logger.warning('{} already processed, skipping.', entry["id"])
                continue
            if "id" in entry and entry["id"] not in already_done:
                todos.append(entry)
            elif isinstance(entry.get("defs", None), list):
                fully_processed = True
                for d in entry["defs"]:
                    if d["id"] not in already_done:
                        fully_processed = False
                        break
                if not fully_processed:
                    result_recorder.remove(entry)
                    todos.append(entry)
                else:
                    logger.warning('{} already processed, skipping.', entry["kanji"] or entry["word"])
                    continue

        return todos



    def start_thread(self):
        self.grammar_sense_thread.start()
        self.grammar_translate_thread.start()
        self.classify_thread.start()
        self.rate_thread.start()
        self.translate_thread.start()
        self.sense_thread.start()
        logger.info('all tasker is prepared')

    def finish(self):
        self.grammar_sense_thread.join()
        self.grammar_translate_thread.join()
        self.classify_thread.join()
        self.rate_thread.join()
        self.translate_thread.join()
        self.sense_thread.join()
        logger.info('all tasker terminated')
        self.pool.put(None)
        self.query_tqdm.close()

    def _entry_done(self, id):
        job_status = [self.rate_status, self.translate_status, self.sense_status, self.classify_status, self.grammar_sense_status, self.grammar_translate_status]
        return all([d.get(id, True) for d in job_status])

    @logger.catch
    def _handle_result(self, tasker_type, result):
        logger.debug('start handle result {}', result['id'])
        with lock:
            id = result["id"]
            processing = {**self.temp[id], **result}
            self.temp[id] = processing
            processing_recorder.update("id", processing)
            self._mark_job_status(tasker_type, id, True)
            if self._entry_done(id):
                p = self.temp.pop(id)
                if not p:
                    logger.error('? no temp entry')
                processing_recorder.remove(p)
                result_recorder.save(p)
                logger.debug('adding result to pool {}', result['id'])
                self.pool.put_nowait(p)
                logger.debug('result added {}', result['id'])

    def handle_response(self, tasker_type, results):
        if results:
            # self._init_query_tqdm()
            # 获取不到在初始化之前的进度。
            if self.query_tqdm:
                self.query_tqdm.update(1)
            for result in results:
                self._handle_result(tasker_type, result)

    def consume(self):
        return self.pool.get()

    def _init_query_tqdm(self):
        if self.query_tqdm:
            return
        try:
            self.grammar_sense_tasker.porter_thread.join()
            self.grammar_translate_tasker.porter_thread.join()
            self.rate_tasker.porter_thread.join()
            self.sense_tasker.porter_thread.join()
            self.classify_tasker.porter_thread.join()
            self.translate_tasker.porter_thread.join()
        except RuntimeError:
            pass
        todo_size = self.rate_tasker.get_queue_size() + self.translate_tasker.get_queue_size() + self.sense_tasker.get_queue_size() + self.classify_tasker.get_queue_size() + self.grammar_translate_tasker.get_queue_size() + self.grammar_sense_tasker.get_queue_size()
        self.query_tqdm = tqdm(total=todo_size)

    def run(self):
        logger.info('start running')
        self.start_thread()

        todos, todos_clone = tee(self.todos)

        print('adding todos')
        logger.info('adding todos')
        thread_map(self.process, todos, total=len(list(todos_clone)))

        print('fetching results from AI')
        logger.info('adding todos')
        self._init_query_tqdm()

        self.finish()

    def _get_sub_dict(self, entry, fields):
        return {k: entry.get(k, '') for k in fields}

    @logger.catch
    def _split_entry(self, entry):
        defs = entry.get('defs', None)
        entry_common_fields = ['word', 'kanji', 'accent', 'dict_type', 'usage']
        def_fields = ["id", "definition", "def_cn", "examples"]
        if defs:
            return map(lambda d: {**self._get_sub_dict(entry, entry_common_fields), **self._get_sub_dict(d, def_fields)}, defs)
        else:
            return iter([self._get_sub_dict(entry, [*entry_common_fields, *def_fields])])

    def _mark_job_status(self, tasker_type, id, status=False):
        status_dict = None
        if tasker_type == RateTasker:
            status_dict = self.rate_status
        elif tasker_type == TranslateTasker:
            status_dict = self.translate_status
        elif tasker_type == SenseTasker:
            status_dict = self.sense_status
        elif tasker_type == ClassifyTasker:
            status_dict = self.classify_status
        elif tasker_type == GrammarSenseTasker:
            status_dict = self.grammar_sense_status
        elif tasker_type == GrammarTranslateTasker:
            status_dict = self.grammar_translate_status

        status_dict[id] = status

    def handle_job(self, tasker, entry, priority):
        self._mark_job_status(type(tasker), entry["id"], False)
        tasker.append(entry, priority=priority)

    @logger.catch
    def _get_handlers(self, entry, first=False):
        handlers = []
        # priority = 1 if first else random.randint(1, 50000)
        priority = random.randint(1, max(2, self.len_unfinished)) if first else random.randint(max(1, self.len_unfinished), 200000)

        if entry["dict_type"] == 'JLPT':
            handlers = [lambda e: self.handle_job(self.grammar_translate_tasker, e, priority)]
            if len(entry["examples"]) < 2:
                handlers.append(lambda e: self.handle_job(self.grammar_sense_tasker, e, priority))

            return handlers


        if "categories" not in entry or not entry["categories"]:
            handlers.append(lambda e: self.handle_job(self.classify_tasker, e, priority))

        if entry["dict_type"] != 'Common_Idioms':
            if "score" not in entry or "reason" not in "entry":
                handlers.append(lambda e: self.handle_job(self.rate_tasker, e, priority))

            if not entry["def_cn"]:
                handlers.append(lambda e: self.handle_job(self.translate_tasker, e, priority))

            if not entry['examples'] or len(entry['examples']) < 3:
                handlers.append(lambda e: self.handle_job(self.sense_tasker, e, priority))

        return handlers

    def _is_safe(self, item):
        if not item:
            return True
        for keyword in self.blacklist:
            if keyword in item:
                return False
        return True

    def process(self, entry):
        sub_entries = self._split_entry(entry)
        for sub_entry in sub_entries:
            if not self._is_safe(sub_entry["definition"]) or not self._is_safe(sub_entry["word"]) or not self._is_safe(sub_entry["kanji"]):
                continue

            is_unfinished = False
            id = sub_entry["id"]
            if id in self.unfinished:
                is_unfinished = True
                logger.warning('found unfinished item {}', self.unfinished[id])
                sub_entry = self.unfinished[id]
            handlers = self._get_handlers(sub_entry, first=is_unfinished)
            for h in handlers:
                self.temp[id] = sub_entry
                h(sub_entry)
