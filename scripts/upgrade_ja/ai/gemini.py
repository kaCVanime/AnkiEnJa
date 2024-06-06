import os
import json
from abc import ABC, abstractmethod

import google.generativeai as genai

from .rate_limiter import rate_limit
from .retry import retry

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class Base(ABC):
    def __init__(self, hint_path):
        with open(hint_path, mode="r", encoding="utf-8") as f:
            content = f.read()
        self.model = genai.GenerativeModel("gemini-1.5-flash-latest", system_instruction=content)

    @abstractmethod
    def construct_question(self, entries):
        pass

    @retry(max_retries=5, delay=3)
    def query(self, entries):
        try:
            resp = self._query(entries)
            text = resp.text
            result = json.loads(text)
            self._validate(result, entries)
            return None, result
        except Exception as e:
            return e, None

    @abstractmethod
    def _query(self, entries):
        pass

    @abstractmethod
    def _validate(self, result, entries):
        if not isinstance(result, list):
            raise Exception("ai response is not a valid list")

        if len(result) != len(entries):
            raise Exception("ai response len doesn't match")

        return True

class Translator(Base):

    def construct_question(self, entries):
        pass

    @rate_limit
    def _query(self, entries):
        question = self.construct_question(entries)
        pass

    def _validate(self, result, entries):
        super()._validate(result, entries)


class Rater(Base):
    def construct_question(self, entries):
        pass

    @rate_limit
    def query(self, entries):
        question = self.construct_question(entries)
        pass

    def _validate(self, result, entries):
        super()._validate(result, entries)
        for item in result:
            if "score" not in item or "culture" not in item or "reason" not in item:
                raise Exception("missing field in ai response item")
        return True

class Senser(Base):
    def construct_question(self, entries):
        pass

    @rate_limit
    def query(self, entries):
        question = self.construct_question(entries)
        pass

    def _validate(self, result, entries):
        super()._validate(result, entries)