import os
import json
from abc import ABC, abstractmethod
from pathlib import Path
from copy import copy

from loguru import logger

import google.generativeai as genai

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

    @staticmethod
    def construct_head(entry):
        word = entry['word']
        kanji = entry['kanji']
        if entry["dict_type"] != 'Common_Idioms':
            return ''.join(filter(None, [word, kanji]))
        return kanji

    def construct_question(self, entries):
        return '\n'.join([f'{idx + 1}. {Base.construct_head(e)} - {e["definition"]}' for idx, e in enumerate(entries)])


    @retry(max_retries=4, delay=3)
    def _query_retry(self, entries):
        logger.info('{} querying gemini', type(self).__name__)
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
        return self.model.generate_content(question, request_options={"timeout": 30.0})

    @abstractmethod
    def _validate(self, result, entries):
        assert isinstance(result, list), "ai response is not a valid list"

        assert len(result) == len(entries), "ai response length doesn't match"

        return True
    
    @abstractmethod
    def preprocess_result(self, results, entries):
        pass


class Translator(Base):
    hint_path = file_path / 'hint_translate_definition.txt'

    def _validate(self, result, entries):
        super()._validate(result, entries)
        for t in result:
            assert isinstance(t, str), "translation is not a valid str"
            
    def preprocess_result(self, results, entries):
        x = []
        for idx, t in enumerate(results):
            entry = entries[idx]
            x.append({
                "id": entry["id"],
                "def_cn": t
            })
        return x


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
            x.append({
                "id": entry["id"],
                "score": item["score"],
                "reason": item["reason"]
            })
        return x


class Senser(Base):
    hint_path = file_path / 'hint_get_more_examples.txt'

    def _validate(self, result, entries):
        super()._validate(result, entries)
        for examples in result:
            assert isinstance(examples, list)
            for eg in examples:
                assert isinstance(eg, dict), "example item is not a valid dict"
                assert "ja" in eg, "missing field: ja"
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
                examples.append({
                    "ja": eg["ja"],
                    "cn": eg["cn"],
                    "name": f'{entry["id"]}_{start + eg_idx}'
                })
                
            x.append({
                "id": entry["id"],
                "examples": examples
            })
        return x
        

class Classifier(Base):
    hint_path = file_path / 'hint_classify.txt'

    classes = [
        "Appearance",
        "Antiques & Collectibles",
        "Architecture",
        "Art",
        "Biography & Autobiography",
        "Body, Mind & Spirit",
        "Business & Economics",
        "Comics & Graphic Novels",
        "Computers",
        "Cooking",
        "Crafts & Hobbies",
        "Communication",
        "Design",
        "Drama",
        "Education",
        "Events & Action",
        "Emotion",
        "Family & Relationships",
        "Fiction",
        "Foreign Language Study",
        "Games & Activities",
        "Gardening",
        "Health & Fitness",
        "History",
        "Humor",
        "Language Arts & Disciplines",
        "Law",
        "Mathematics",
        "Medical",
        "Media",
        "Miscellaneous",
        "Music",
        "Nature",
        "Performing Arts",
        "Personality",
        "Perception",
        "Philosophy",
        "Photography",
        "Political Science",
        "Psychology",
        "Reference",
        "Religion",
        "Science",
        "Social Science",
        "Sports & Recreation",
        "Technology & Engineering",
        "Transportation",
        "Travel"
    ]

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
            headers = [f'{e["kanji"] or e["word"]}: {e["definition"]};  ' for e in entries]
            logger.warning('AI is inventing classes {} for {}', new_cls, ''.join(headers))
            
    def preprocess_result(self, results, entries):
        x = []
        for idx, t in enumerate(results):
            entry = entries[idx]
            x.append({
                "id": entry["id"],
                "categories": t
            })
        return x
