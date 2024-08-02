from pathlib import Path
from src.utils import Recorder
from loguru import logger

recorder = Recorder()
main_db_file = Path.cwd().parent / 'upgrade_en' / 'src' / 'assets' / 'upgrade.db'

@ logger.catch
def main():
    recorder.init_todos(main_db_file)


if __name__ == '__main__':
    recorder.start()
    main()
    recorder.close()