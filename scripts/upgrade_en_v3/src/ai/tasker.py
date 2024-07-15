from abc import ABC, abstractmethod
from .gemini import Rater, Translator, Senser, Classifier, DefTranslator, SynonymSensor
from threading import Thread, Event
from loguru import logger
import queue
from dataclasses import dataclass, field
from typing import Any
import random

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class Base(ABC):
    capacity = 10
    def __init__(self, parent, ai):

        self._parent = parent
        self._ai = ai

        self._buffer = queue.PriorityQueue()
        self._queue = queue.Queue()

        self._start = Event()
        self._queue_done = Event()

        self.porter_thread = Thread(target=self.porter, daemon=True)
        self._queryer_thread = Thread(target=self.queryer, daemon=True)

    def run(self):
        self._start.wait()
        self.porter_thread.start()
        self._queryer_thread.start()
        self._queue_done.wait()
        logger.info('tasker {} terminated', type(self).__name__)

    @logger.catch
    def porter(self):
        logger.info('{}: thread porter started', type(self).__name__)
        while True:
            todos = []
            try:
                for i in range(self.capacity):
                    logger.debug('{}: fetching from buffer', type(self).__name__)
                    p_item = self._buffer.get(block=True, timeout=10)
                    item = p_item.item
                    todos.append(item)
                logger.debug('{}: porting {}', type(self).__name__, [t.get("usage", "") or t.get("word", "") for t in todos])
                self._queue.put(todos)
            except queue.Empty:
                if todos:
                    self._queue.put(todos)
                self._queue.put(None)
                logger.info('{}: porter terminated', type(self).__name__)
                break

    @logger.catch
    def queryer(self):
        logger.info('{}: thread queryer started', type(self).__name__)
        while True:
            logger.debug('{}: thread queryer fetching entries', type(self).__name__)
            entries = self._queue.get()
            self._queue.task_done()
            logger.debug('{}: thread queryer got entries: {}', type(self).__name__, [t.get("usage", "") or t.get("word", "")  for t in entries] if entries else None)
            if not entries:
                logger.info('{}: thread queryer terminated', type(self).__name__)
                self._queue_done.set()
                break
            err, result = self._ai.query(entries)
            if err:
                self.response(None)
            else:
                self.response(result)


    def append(self, entry, priority):
        self._buffer.put(PrioritizedItem(priority=priority or random.randint(1, 50000), item=entry))
        self._start.set()

    def force_start(self):
        self._start.set()

    def is_start(self):
        return self._start.is_set()

    def response(self, result):
        self._parent.handle_response(type(self), result)

    def get_queue_size(self):
        return self._queue.qsize()


class ClassifyTasker(Base):
    def __init__(self, parent):
        super().__init__(parent, Classifier())


class RateTasker(Base):
    def __init__(self, parent):
        super().__init__(parent, Rater())

class TranslateTasker(Base):
    capacity = 4
    def __init__(self, parent):
        super().__init__(parent, Translator())


class SenseTasker(Base):
    capacity = 7
    def __init__(self, parent):
        super().__init__(parent, Senser())


class DefTranslateTasker(Base):
    def __init__(self, parent):
        super().__init__(parent, DefTranslator())


class SynonymSenseTasker(Base):
    capacity = 1
    def __init__(self, parent):
        super().__init__(parent, SynonymSensor())

