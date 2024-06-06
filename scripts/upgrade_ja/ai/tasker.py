from abc import ABC, abstractmethod
from .gemini import Rater, Translator, Senser
from threading import Thread, Event
import queue



class Base(ABC):
    capacity = 10
    def __init__(self, parent, ai):
        self.parent = parent
        self.buffer = queue.Queue(self.capacity)
        self.queue = queue.Queue()
        self.ai = ai
        self._start = Event()
        self._porter_thread = Thread(target=self.porter, daemon=True)
        self._queryer_thread = Thread(target=self.queryer, daemon=True)

    def run(self):
        self._start.wait()
        self._porter_thread.start()
        self._queryer_thread.start()
        self.queue.join()
        self.finish()

    def porter(self):
        while True:
            todos = []
            try:
                for i in range(self.capacity):
                    todos.append(self.buffer.get(block=True, timeout=3))
            except queue.Empty:
                break
            finally:
                self.queue.put(todos)

    def queryer(self):
        self._porter_thread.join()
        while True:
            entries = self.queue.get()
            result = self.ai.query(entries)
            self.response(result)
            self.queue.task_done()
            if self.queue.empty():
                break


    def append(self, entry):
        self.buffer.put(entry)
        self._start.set()

    def finish(self):
        self.parent.finish_task(type(self))

    def response(self, result):
        self.parent.handle_response(type(self), result)


class RateTasker(Base):
    def __init__(self, parent, hint_path):
        super().__init__(parent, Rater(hint_path))



class TranslateTasker(Base):
    def __init__(self, parent, hint_path):
        super().__init__(parent, Translator(hint_path))


class SenseTasker(Base):
    def __init__(self, parent, hint_path):
        super().__init__(parent, Senser(hint_path))




