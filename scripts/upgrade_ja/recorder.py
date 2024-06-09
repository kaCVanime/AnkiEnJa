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

    def save(self, entry):
        self._results.append(entry)
        logger.debug('saving {} to {}', entry, self.name)
        with self.lock:
            with open(self.file, mode='wb') as f:
                pickle.dump(self._results, f)
