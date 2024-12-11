import random
import json
from src.ai.qwen.qwen import preprocess_response

def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile, 2):
        if random.randrange(num):
            continue
        line = aline
    return line

with open('batch_results/rate0.jsonl', 'r', encoding='utf-8') as f:
    line = random_line(f)
    obj = json.loads(line)
    pass
    result = obj["response"]["body"]["choices"][0]["message"]["content"]
    print(preprocess_response(result))
    print('-----------------')
    print(obj["custom_id"])
    print(result)

