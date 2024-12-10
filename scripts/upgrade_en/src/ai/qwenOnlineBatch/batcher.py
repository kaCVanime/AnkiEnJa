import threading
import sys
from pathlib import Path

from ..qwen.qwen import Translator, Senser, Rater

lock = threading.Lock()

batch_path = Path('./batch')
batch_path.mkdir(exist_ok=True)

class Batcher:
    def __init__(self, name):
        self.name = name

    def write(self, content):
        with lock:
            fp = self.get_fp(content)
            fp.write(content + '\n')
            fp.close()

    def config(self, content):
        pass

    def get_fp(self, content):
        i = 0
        sz_content = sys.getsizeof(content)
        while True:
            p = batch_path / f'{self.name}{i}.jsonl'

            fp = open(p, 'a', encoding='utf-8')
            sz_file = fp.tell()

            if sz_file + sz_content >= 100 * 1024 * 1024:
                fp.close()
                i += 1
                continue

            return fp


class TranslateBatcher(Translator, Batcher):
    name = 'translate'
    top_p = 0.8
    temperature = 0.7
    def __init__(self):
        Translator.__init__(self)
        Batcher.__init__(self, self.name)
        
class SenseBatcher(Senser, Batcher):
    name = 'sense'
    top_p = 0.8
    temperature = 0.7
    def __init__(self):
        SenseBatcher.__init__(self)
        Batcher.__init__(self, self.name)
        
class RateBatcher(Rater, Batcher):
    name = 'rate'
    top_p = 0.2
    temperature = 0.3
    def __init__(self):
        Rater.__init__(self)
        Batcher.__init__(self, self.name)