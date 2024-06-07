from abc import ABC, abstractmethod
from .gemini import Rater, Translator, Senser
from threading import Thread, Event
from loguru import logger
import queue




class Base(ABC):
    capacity = 10
    def __init__(self, parent, ai):
        # logger.remove()
        # logger.add('ai.log')

        self._parent = parent
        self._ai = ai

        self._buffer = queue.Queue(self.capacity)
        self._queue = queue.Queue()

        self._start = Event()

        self._porter_thread = Thread(target=self.porter, daemon=True)
        self._queryer_thread = Thread(target=self.queryer, daemon=True)

    def run(self):
        self._start.wait()
        self._porter_thread.start()
        self._queryer_thread.start()
        self._queue.join()
        logger.info('tasker {} terminated', type(self).__name__)

    @logger.catch
    def porter(self):
        logger.info('thread porter started')
        while True:
            todos = []
            try:
                for i in range(self.capacity):
                    logger.debug('fetching from buffer')
                    todos.append(self._buffer.get(block=True, timeout=3))
                logger.debug('porting {}', todos)
                self._queue.put(todos)
            except queue.Empty:
                if todos:
                    self._queue.put(todos)
                self._queue.put(None)
                logger.info('porter terminated')
                break

    @logger.catch
    def queryer(self):
        logger.info('thread queryer started')
        while True:
            entries = self._queue.get()
            self._queue.task_done()
            if not entries:
                logger.info('queryer terminated')
                break
            err, result = self._ai.query(entries)
            if err:
                logger.error(err)
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




