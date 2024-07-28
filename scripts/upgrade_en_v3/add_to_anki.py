from loguru import logger
from src.anki.manager import AnkiManager, results_recorder


logger.remove()
logger.add('add_to_anki.log', level='INFO')

results_recorder.start()
m = AnkiManager('KEXP2')

m.run()