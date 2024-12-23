import random
import json


def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile, 2):
        if random.randrange(num):
            continue
        line = aline
    return line

with open('batch/translate0.jsonl', 'r', encoding='utf-8') as f:
    line = random_line(f)
    obj = json.loads(line)
    print(
            f'''top_p: {obj["top_p"]}
temperature: {obj["temperature"]}
{obj["body"]["messages"][1]["content"]}
    '''
    )
    # print('------------')
    # print(obj["body"]["messages"][0]["content"])
