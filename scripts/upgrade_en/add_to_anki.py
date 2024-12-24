from loguru import logger
from src.anki.manager import AnkiManager


logger.remove()
logger.add('add_to_anki.log', level='INFO')

m = AnkiManager('KEXP3')

m.run()