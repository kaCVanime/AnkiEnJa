import random
import json
from collections import defaultdict
def random_line(afile):
    line = next(afile)
    for num, aline in enumerate(afile, 2):
        if random.randrange(num):
            continue
        line = aline
    return line

class ResultParser:
    input_k_price = 4e-4
    output_k_price = 1e-3
    def __init__(self, fp):
        if type(fp) is not list:
            fp = [fp]
        self.fp = fp

    def get_raw_from_obj(self, obj):
        return obj["response"]["body"]["choices"][0]["message"]["content"]

    def get_result_from_raw(self, raw):
        from ..qwen.qwen import preprocess_response
        return preprocess_response(raw)

    def get_result(self, jsol):
        return self.get_result_from_raw(self.get_raw_from_obj(json.loads(jsol)))

    def calc_price(self):
        total_input = 0
        total_output = 0

        for fp in self.fp:
            with open(fp, 'r', encoding='utf-8') as f:
                for l in f:
                    obj = json.loads(l)
                    usage = obj["response"]["body"]["usage"]
                    total_input += usage['prompt_tokens']
                    total_output += usage['completion_tokens']

        return {
            "price": self.input_k_price * 1e-3 * total_input + self.output_k_price * 1e-3 * total_output,
            "total_input_tks": total_input,
            "total_output_tks": total_output
        }

class RateParser(ResultParser):
    def __init__(self, fp):
        super().__init__(fp)

    def get_stats(self):
        from ..qwen.qwen import Rater
        rater = Rater()
        rates = defaultdict(lambda: 0)

        for fp in self.fp:
            with open(fp, 'r', encoding='utf-8') as f:
                for l in f:
                    obj = json.loads(l)
                    try:
                        result = self.get_result_from_raw(self.get_raw_from_obj(obj))
                        rater.validate(result)
                        rates[f'{result["sense"].upper()}-{result["word"].upper()}'] += 1
                    except Exception as e:
                        print(obj["custom_id"])
                        print(e)

        return rates


    def get_random_result(self):
        fp = self.fp[random.randrange(0, len(self.fp))]
        with open(fp, 'r', encoding='utf-8') as f:
            line = random_line(f)
            obj = json.loads(line)
            raw = self.get_raw_from_obj(obj)
            print(self.get_result_from_raw(raw))
            print('-----------------')
            print(obj["custom_id"])
            print(raw)