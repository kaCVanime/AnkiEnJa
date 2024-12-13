import random
import json
from src.ai.qwenOnlineBatch.result_parser import RateParser

fp = 'batch_results/test1w.jsonl'

rate_parser = RateParser(fp)



if __name__ == '__main__':
    # print(rate_parser.get_stats())
    rate_parser.get_random_result()
    pass