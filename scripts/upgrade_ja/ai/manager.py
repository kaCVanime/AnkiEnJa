import json
import logging
from time import sleep

from tqdm.contrib.concurrent import thread_map

logging.basicConfig(
    filename="ai.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    encoding='utf-8'
)
logger = logging.getLogger(__name__)



class ResultIterator:
    def __init__(self, todos):
        self.manager = Manager(todos)
        self.manager.start()
        self.enhanced = None

    def __iter__(self):
        if self.manager.results:
            self.enhanced = iter(self.manager.results)
        return self

    def __next__(self):
        if self.enhanced:
            return next(self.enhanced)

        result = self.manager.consume()
        if not result:
            raise StopIteration
        return result


class Manager:
    def __init__(self, todos):
        self.results = []
        self.todos = todos
        self.pool = []
        self.done = False

        self.rate_queue = []
        self.translate_queue = []
        self.more_egs_queue = []

    def get_entry_type(self, entry):
        pass

    def consume(self):
        if self.pool:
            return self.pool.pop(0)
        elif self.done:
            return None
        else:
            sleep(3)
            return self.consume()

    def start(self):
        print('start processing entries')
        thread_map(self.process, self.todos)

    def _get_sub_dict(self, entry, fields):
        return {k: entry[k] for k in fields}

    def _split_entry(self, entry):
        defs = entry.get('defs', None)
        entry_common_fields = ['word', 'kanji', 'accent', 'dict_type']
        def_fields = ["id", "definition", "def_cn", "examples"]
        if defs:
            return map(lambda d: {**self._get_sub_dict(entry, entry_common_fields), **self._get_sub_dict(d, def_fields), }, defs)
        else:
            return iter([self._get_sub_dict(entry, [*entry_common_fields, *def_fields])])


    def handle_rate(self, entry):
        pass

    def handle_translate_def_and_egs(self, entry):
        pass

    def handle_get_more_egs(self, entry):
        pass

    def _get_handlers(self, entry):
        handlers = [self.handle_rate]

        if not entry["def_cn"]:
            handlers.append(self.handle_translate_def_and_egs)

        if len(entry['examples']) < 4:
            handlers.append(self.handle_get_more_egs)

        return handlers

    def process(self, entry):
        sub_entries = self._split_entry(entry)

        for se in sub_entries:
            handlers = self._get_handlers(se)
            for h in handlers:
                h(se)

