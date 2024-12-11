import os
import threading
import sys
import json
from pathlib import Path

from ..qwen.qwen import Translator, Senser, Rater

lock = threading.Lock()

batch_path = Path('./batch')
batch_path.mkdir(exist_ok=True)

class Batcher:
    top_p = None
    temperature = None
    def __init__(self, name):
        self.name = name

    def write(self, content):
        with lock:
            fp = self.get_fp(content)
            fp.write(content + '\n')
            fp.close()


    def get_fp(self, content):
        i = 0
        sz_content = sys.getsizeof(content)
        while True:
            p = batch_path / f'{self.name}{i}.jsonl'

            fp = open(p, 'a+', encoding='utf-8')
            sz_file = fp.tell()
            fp.seek(0)
            num_lines = sum(1 for _ in fp)

            if num_lines >= 5e4 - 2 or sz_file + sz_content >= 100 * 1024 * 1024:
                fp.close()
                i += 1
                continue

            return fp


    def make_query(self, id, instruction, message):
        query = {
            "custom_id": id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "top_p": self.top_p,
            "temperature": self.temperature,
            "body": {
                "model": "qwen-plus",
                "messages": [
                    {
                        "role": "system",
                        "content": instruction
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
        }
        return json.dumps(query, ensure_ascii=False)

    def handle(self, id, instruction, message):
        self.write(self.make_query(id, instruction, message))


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
        Senser.__init__(self)
        Batcher.__init__(self, self.name)
        
class RateBatcher(Rater, Batcher):
    name = 'rate'
    top_p = 0.2
    temperature = 0.3
    def __init__(self):
        Rater.__init__(self)
        Batcher.__init__(self, self.name)