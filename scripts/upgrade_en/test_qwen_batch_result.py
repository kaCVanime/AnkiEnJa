from pathlib import Path
from src.ai.qwenOnlineBatch.result_parser import RateParser

files = list(Path('./batch_results').glob('?.jsonl'))

# fp = 'batch_results/test1w.jsonl'


rate_parser = RateParser(files)



if __name__ == '__main__':
    # print(rate_parser.get_stats())
    rate_parser.get_random_result()
    # rate_parser.write()
    pass