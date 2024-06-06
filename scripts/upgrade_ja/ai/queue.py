from abc import ABC, abstractmethod
from pathlib import Path
from .gemini import Rater, Translator, Senser
from threading import Lock
lock = Lock()

rater_hint_path = Path('.zxc.tex')
translator_hint_path = Path('.zxc.tex')
sensor_hint_path = Path('.zxc.tex')

class Base(ABC):
    capacity = 10
    def __init__(self, parent, ai, hint_path):
        self.parent = parent
        self.buffer = []
        self.ai = ai(hint_path)

    def append(self, entry):
        self.buffer.append(entry)
        with lock:
            if len(self.buffer) > self.capacity:
                results = self.ai.query(self.buffer)
                self.buffer.clear()
                self.parent.ai_callback(type(self), results)



class RaterQueue(Base):
    def __init__(self, parent):
        super().__init__(parent, Rater, rater_hint_path)

class TranslatorQueue(Base):
    def __init__(self, parent):
        super().__init__(parent, Translator, translator_hint_path)

class SenserQueue(Base):
    def __init__(self, parent):
        super().__init__(parent, Senser, sensor_hint_path)




