import pickle
from pathlib import Path

from loguru import logger



record_file = Path(__file__).parent / 'results.pkl'

class Recorder:
    def __init__(self, file=record_file):
        self.file = file
        self._results = []
        if Path(file).is_file():
            with open(self.file, mode='rb') as f:
                self._results = pickle.load(f)

    def get(self):
        return self._results

    def save(self, entry):
        logger.debug('saving {}', entry)
        self._results.append(entry)
        with open(self.file, mode='wb') as f:
            pickle.dump(self._results, f)
