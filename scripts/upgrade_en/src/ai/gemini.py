import os
import json
from abc import ABC, abstractmethod
from pathlib import Path
from copy import copy, deepcopy

from loguru import logger

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted

from .rate_limiter import rate_limit
from .retry import retry

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

file_path = Path(__file__).parent


def preprocess_response(text):
    text = text.strip()
    if text.startswith('```'):
        text = text[3:]
        text = text.strip()
    if text.endswith('```'):
        text = text[:-3]
        text = text.strip()
    if text.startswith('json'):
        text = text[4:]
        text = text.strip()
    return text


class TestResponse:
    def __init__(self, content):
        self.text = content


class Base(ABC):
    hint_path = None

    def __init__(self):

        with open(self.hint_path, mode="r", encoding="utf-8") as f:
            content = f.read()
        self.model = genai.GenerativeModel("gemini-1.5-flash-latest", system_instruction=content)

    def construct_question(self, entries):
        return '\n'.join(
            [f'{idx + 1}. {e.get("word", "")} - {e["definition"]}.' for idx, e in
             enumerate(entries)]
        )

    @retry(max_retries=4, delay=3, exit_errors=[ResourceExhausted])
    def _query_retry(self, entries):
        logger.debug('{} querying gemini', type(self).__name__)
        entries = self.preprocess_entries(entries)
        resp = self._query(entries)
        text = preprocess_response(resp.text)
        logger.debug('{}: Response received. {}', type(self).__name__, text)
        result = json.loads(text)
        self._validate(result, entries)
        result = self.preprocess_result(result, entries)
        return None, result

    @logger.catch
    def query(self, entries):
        try:
            return self._query_retry(entries)
        except Exception as e:
            logger.error(e)
            return e, None

    @rate_limit
    def _query(self, entries):
        logger.debug('{}: construct question from {}', type(self).__name__, entries)
        question = self.construct_question(entries)
        logger.debug('{}: question: {}', type(self).__name__, question)
        return self.model.generate_content(
            question,
            request_options={"timeout": 30.0},
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH
            }
        )

    @abstractmethod
    def _validate(self, result, entries):
        assert isinstance(result, list), "ai response is not a valid list"

        assert len(result) == len(entries), "ai response length doesn't match"

        return True

    @abstractmethod
    def preprocess_result(self, results, entries):
        pass

    def preprocess_entries(self, entries):
        return entries


class Translator(Base):
    hint_path = file_path / 'hint_translate.txt'

    def _validate(self, results, entries):
        super()._validate(results, entries)
        for idx, t in enumerate(results):
            assert "word" in t, "missing key: word"
            assert "examples" in t, "missing key: examples"

            entry = entries[idx]
            assert len(t["examples"]) == len([x["en"] for x in entry["examples"] if x.get("ai", False)]), "examples length not matching"


    def construct_question(self, entries):
        p = [
            {
                "word": r.get("word"),
                "definition": r["definition"],
                "examples": [x["en"] for x in r["examples"] if x.get("ai", False)]
            }
            for r in entries
        ]
        return json.dumps(p, indent=4, ensure_ascii=False)

    def preprocess_result(self, results, entries):
        x = []
        for idx, t in enumerate(results):
            entry = deepcopy(entries[idx])
            ai_egs = list(filter(lambda eg: eg.get("ai", False), entry["examples"]))
            for idx, eg in enumerate(t["examples"]):
                ai_egs[idx]["cn"] = eg
            x.append(
                {
                    "id": entry["id"],
                    "examples": entry["examples"]
                }
            )
        return x


class DefTranslator(Base):
    hint_path = file_path / 'hint_translate_definition.txt'

    def _validate(self, result, entries):
        super()._validate(result, entries)

    def preprocess_result(self, results, entries):
        return [{"id": entries[idx]["id"], "def_cn": r} for idx, r in enumerate(results)]

class Rater(Base):
    hint_path = file_path / 'hint_rate.txt'

    def _validate(self, result, entries):
        super()._validate(result, entries)
        for item in result:
            assert isinstance(item, dict), "rate item is not a valid dict"
            assert "score" in item, "missing field: score"
            assert "reason" in item, "missing field: reason"

    def preprocess_result(self, results, entries):
        x = []
        for idx, item in enumerate(results):
            entry = entries[idx]
            x.append(
                {
                    "id": entry["id"],
                    "score": item["score"],
                    "reason": item["reason"]
                }
            )
        return x


class Senser(Base):
    hint_path = file_path / 'hint_get_more_examples.txt'

    def _validate(self, result, entries):
        super()._validate(result, entries)
        for examples in result:
            assert isinstance(examples, list)
            for eg in examples:
                assert isinstance(eg, dict), "example item is not a valid dict"
                assert "en" in eg, "missing field: en"
                assert "cn" in eg, "missing field: cn"

    def preprocess_result(self, results, entries):
        x = []
        for idx, items in enumerate(results):
            entry = entries[idx]
            examples = copy(entry["examples"])
            if isinstance(examples, list):
                start = len(examples)
            else:
                examples = []
                start = 0

            for eg_idx, eg in enumerate(items):
                examples.append(
                    {
                        "en": eg["en"],
                        "cn": eg["cn"],
                        "name": f'{entry["id"]}_{start + eg_idx}',
                        "ai": True,
                        "en_ai": True
                    }
                )

            x.append(
                {
                    "id": entry["id"],
                    "examples": examples
                }
            )
        return x


class Classifier(Base):
    hint_path = file_path / 'hint_classify.txt'

    classes = ['Animals', 'Birds', 'Fish and shellfish', 'Insects, worms, etc.', 'Appearance', 'Body',
               'Clothes and Fashion', 'Colours and Shapes', 'Language', 'Phones, email and the internet', 'Art',
               'Film and theatre', 'Literature and writing', 'Music', 'TV, radio and news', 'Cooking and eating',
               'Drinks', 'Food', 'Discussion and agreement', 'Doubt, guessing and certainty', 'Opinion and argument',
               'Permission and obligation', 'Preferences and decisions', 'Suggestions and advice', 'Disability',
               'Health and Fitness', 'Health problems', 'Healthcare', 'Mental health', 'Buildings', 'Gardens',
               'Houses and homes', 'Games & Activities', 'Hobbies', 'Shopping', 'Change, cause and effect', 'Danger',
               'Difficulty and failure', 'Success', 'Education', 'Family and relationships', 'Feelings', 'Life stages',
               'Personal qualities', 'Events & Actions', 'Crime and punishment', 'Law and justice', 'People in society',
               'Politics', 'Religion and festivals', 'Social issues', 'War and conflict', 'Biology', 'Computers',
               'Engineering', 'Maths and measurement', 'Physics and chemistry', 'Scientific research',
               'Sports: ball and racket sports', 'Sports: other sports', 'Sports: water sports', 'Farming', 'Geography',
               'Plants and trees', 'The environment', 'Weather', 'History', 'Space', 'Time', 'Holidays',
               'Transport by air', 'Transport by bus and train', 'Transport by car or lorry', 'Transport by water',
               'Business', 'Jobs', 'Money', 'Working life']

    def _validate(self, result, entries):
        super()._validate(result, entries)
        new_cls = []
        for clss in result:
            assert isinstance(clss, list), "clss is not a valid list"
            for cls in clss:
                assert isinstance(cls, str), "cls is not a valid str"
                if cls not in self.classes:
                    new_cls.append(cls)

        if new_cls:
            headers = [f'{e["id"]};  ' for e in entries]
            logger.warning('AI is inventing classes {} for {}', new_cls, ''.join(headers))

    def preprocess_result(self, results, entries):
        x = []
        for idx, t in enumerate(results):
            entry = entries[idx]
            x.append(
                {
                    "id": entry["id"],
                    "topic": "=_=".join(t)
                }
            )
        return x


class SynonymSensor(Base):
    hint_path = file_path / 'hint_sense_synonyms.txt'

    def flatten_list(self, l):
        result = []

        for item in l:
            if isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)
        return result

    def preprocess_entries(self, entry):
        assert isinstance(entry, list)
        assert len(entry) == 1
        entry = entry[0]
        return {
            "id": entry["id"],
            "words": entry["words"],
            "dict_type": entry["dict_type"],
            "defs": self.flatten_list(entry["defs"])
        }
    def _validate(self, results, entry):
        assert len(results) == len(entry["defs"]), "defs length not match"
        for egs in results:
            assert len(egs) == 3, "incorrect examples length"
            for eg in egs:
                assert "en" in eg, "missing field: en"
                assert "cn" in eg, "missing field: cn"


    def construct_question(self, entry):
        defs = '\n'.join([
            f'{idx + 1}. {t["definition"]}'
            for idx, t in enumerate(entry["defs"])
        ])
        return f'''
            topic: {entry["words"]}
            {defs}
        '''

    def preprocess_result(self, results, entry):
        for idx, egs in enumerate(results):
            d = entry["defs"][idx]
            start = len(d["examples"])
            d["examples"].extend(
                [
                    {
                        **eg,
                        "name": f'{d["id"]}_{ei+start}',
                        "usage": "",
                        "labels": "",
                        "ai": True
                    }
                    for ei, eg in enumerate(egs)
                ]
            )

        return [entry]


