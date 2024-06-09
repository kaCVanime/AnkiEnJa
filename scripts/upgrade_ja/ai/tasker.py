from abc import ABC, abstractmethod
from .gemini import Rater, Translator, Senser
from threading import Thread, Event
from loguru import logger
import queue




class Base(ABC):
    capacity = 10
    def __init__(self, parent, ai):

        self._parent = parent
        self._ai = ai

        self._buffer = queue.Queue(self.capacity)
        self._queue = queue.Queue()

        self._start = Event()
        self._queue_done = Event()

        self._porter_thread = Thread(target=self.porter, daemon=True)
        self._queryer_thread = Thread(target=self.queryer, daemon=True)

    def run(self):
        self._start.wait()
        self._porter_thread.start()
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
                    todos.append(self._buffer.get(block=True, timeout=3))
                logger.debug('{}: porting {}', type(self).__name__, todos)
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
            logger.info('{}: thread queryer fetching entries', type(self).__name__)
            entries = self._queue.get()
            self._queue.task_done()
            logger.info('{}: thread queryer got entries', type(self).__name__)
            if not entries:
                logger.info('{}: thread queryer terminated', type(self).__name__)
                self._queue_done.set()
                break
            err, result = self._ai.query(entries)
            if err:
                logger.error('{}: {}', type(self).__name__, err)
            else:
                self.response(self.preprocess_result(result, entries))

    @abstractmethod
    def preprocess_result(self, results, entries):
        pass

    def append(self, entry):
        self._buffer.put(entry)
        self._start.set()

    def response(self, result):
        self._parent.handle_response(type(self), result)

    def get_queue_size(self):
        return self._queue.qsize()


class RateTasker(Base):
    def __init__(self, parent):
        super().__init__(parent, Rater())

    def preprocess_result(self, results, entries):
        return results


class TranslateTasker(Base):
    def __init__(self, parent):
        super().__init__(parent, Translator())

    def preprocess_result(self, results, entries):
        return results


class SenseTasker(Base):
    def __init__(self, parent):
        super().__init__(parent, Senser())

    def preprocess_result(self, results, entries):
        return results




