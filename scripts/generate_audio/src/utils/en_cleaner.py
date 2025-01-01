import re
import json


def main(note):
    if note["examples"]:
        results = []
        examples = json.loads(note["examples"])
        pattern = "^[A-Za-z0-9!+±^<>_﹘*`½₂¼²-⁸♥′″÷∞ξ#@π℃℉×™=?₃,:.…%;\s’‘&“”—'\" ​£$€°\–\-\−]+$"
        # ban_pattern = "[\\\/\[\](){}éôíöèêâáãàñçëî]"
        for eg in examples:
            # There is a dog (= an animal). -> There is a dog.
            en = re.sub('\s?\(.+\)', '', eg["en"])

            if re.match(pattern, en):
                results.append({"name": eg["name"], "eg": en})

        return results