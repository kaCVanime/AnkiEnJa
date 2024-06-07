from loguru import logger
from queue import Queue
from threading import Lock, Thread
from tqdm.contrib.concurrent import thread_map

from .tasker import RateTasker, TranslateTasker, SenseTasker
from ..recorder import Recorder

result_recorder = Recorder()

lock = Lock()




class ResultIterator:
    def __init__(self, todos):
        # logger.remove()
        # logger.add('ai.log')
        self.manager = Manager(todos)
        Thread(target=self.manager.run, daemon=False).start()

    def __iter__(self):
        self.items = iter(result_recorder.get())
        return self

    def __next__(self):
        try:
            return next(self.items)
        except StopIteration:
            result = self.manager.consume()
            logger.debug('result retrieved. {}', result)
            if not result:
                raise StopIteration
            return result


class Manager:
    def __init__(self, todos):
        # already_done = [r["id"] for r in result_recorder.get()]
        # split_entries = [self._split_entry(t) for t in todos]
        # self.todos = iter([t for t in split_entries if t["id"] not in already_done])
        self.todos = todos

        self.pool = Queue()

        self.rate_tasker = RateTasker(self)
        self.rate_thread = Thread(target=self.rate_tasker.run, daemon=True)

        self.translate_tasker = TranslateTasker(self)
        self.translate_thread = Thread(target=self.translate_tasker.run, daemon=True)

        self.sense_tasker = SenseTasker(self)
        self.sense_thread = Thread(target=self.sense_tasker.run, daemon=True)

        self.rate_status = {}
        self.translate_status = {}
        self.sense_status = {}

        self.temp = {}

    def start_thread(self):
        self.rate_thread.start()
        self.translate_thread.start()
        self.sense_thread.start()
        logger.info('all tasker is prepared')

    def finish(self):
        self.rate_thread.join()
        self.translate_thread.join()
        self.sense_thread.join()
        self.pool.put(None)
        logger.info('all tasker terminated')

    def _entry_done(self, id):
        job_status = [self.rate_status, self.translate_status, self.sense_status]
        return all([d.get(id, True) for d in job_status])

    def _handle_result(self, tasker_type, result):
        with lock:
            id = result["id"]
            self.temp[id] = {**self.temp[id], **result}
            self._mark_job_status(tasker_type, id, True)
            if self._entry_done(id):
                p = self.temp.pop(id)
                result_recorder.save(p)
                self.pool.put(p)

    def handle_response(self, tasker_type, results):
        for result in results:
            self._handle_result(tasker_type, result)

    def consume(self):
        return self.pool.get()

    def run(self):
        logger.info('start running')
        self.start_thread()

        thread_map(self.process, self.todos)

        self.finish()

    def _get_sub_dict(self, entry, fields):
        return {k: entry[k] for k in fields}

    @logger.catch
    def _split_entry(self, entry):
        defs = entry.get('defs', None)
        entry_common_fields = ['word', 'kanji', 'accent', 'dict_type']
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
        status_dict[id] = status

    def handle_job(self, tasker, entry):
        self._mark_job_status(type(tasker), entry["id"], False)
        tasker.append(entry)

    @logger.catch
    def _get_handlers(self, entry):
        handlers = [lambda e: self.handle_job(self.rate_tasker, e)]

        if not entry["def_cn"]:
            handlers.append(lambda e: self.handle_job(self.translate_tasker, e))

        if not entry['examples'] or len(entry['examples']) < 3:
            handlers.append(lambda e: self.handle_job(self.sense_tasker, e))

        return handlers

    def process(self, entry):
        # handlers = self._get_handlers(entry)
        # for h in handlers:
        #     logger.debug(entry)
        #     self.temp[entry["id"]] = entry
        #     h(entry)

        sub_entries = self._split_entry(entry)
        for sub_entry in sub_entries:
            handlers = self._get_handlers(sub_entry)
            for h in handlers:
                logger.debug(sub_entry)
                self.temp[sub_entry["id"]] = sub_entry
                h(sub_entry)
