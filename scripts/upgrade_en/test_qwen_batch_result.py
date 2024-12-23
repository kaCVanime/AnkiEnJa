from pathlib import Path
from src.ai.qwenOnlineBatch.result_parser import RateParser, SenseParser, TranslateParser

sense_files = list(Path('./batch_results').glob('sense*.jsonl'))
translate_files = list(Path('./batch_results').glob('translate*.jsonl'))
rate_files = list(Path('./batch_results').glob('?.jsonl'))

# sense_parser = SenseParser(sense_files)
# rate_parser = RateParser(rate_files)
translate_parser = TranslateParser(translate_files)


if __name__ == '__main__':
    # print(rate_parser.get_stats())
    # translate_parser.get_random_result()
    # rate_parser.write()
    # sense_parser.write()
    translate_parser.write()
    pass