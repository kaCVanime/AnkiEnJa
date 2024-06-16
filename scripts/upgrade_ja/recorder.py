import pickle
from pathlib import Path
from loguru import logger
from threading import Lock


cur_dir = Path(__file__).parent


class Recorder:
    def __init__(self, file):
        self.file = Path(file)
        self.file.parent.mkdir(exist_ok=True)
        self.name = self.file.stem
        self._results = []
        self.lock = Lock()
        if Path(file).is_file():
            with open(self.file, mode='rb') as f:
                self._results = pickle.load(f)

    def get(self):
        return self._results

    def remove(self, item):
        if item in self._results:
            logger.debug('removing {}', item)
            self._results.remove(item)

    def remove_by_key(self, key, value):
        todos = filter(lambda t: t[key] == value, self._results)
        for todo in todos:
            self.remove(todo)


    def update(self, key, entry):
        self._results = [entry if t[key] == entry[key] else t for t in self._results]
        if entry not in self._results:
            self.save(entry)
            return
        logger.debug('updating {} to {}', entry[key], entry)
        with self.lock:
            with open(self.file, mode='wb') as f:
                pickle.dump(self._results, f)

    def save(self, entry):
        self._results.append(entry)
        logger.debug('saving {} to {}', entry, self.name)
        with self.lock:
            with open(self.file, mode='wb') as f:
                pickle.dump(self._results, f)
