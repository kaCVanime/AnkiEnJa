import json
import re
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from copy import copy, deepcopy

from loguru import logger

from ..rate_limiter import rate_limit
from ..retry import retry

instruction_path = Path(__file__).parent / 'instructions'


def query_qwen(instruction, message):
    r = requests.post(
        'http://localhost:8080/v1/chat/completions',
        headers={
            "Authorization": "Bearer no-key"
        },
        timeout=300,
        json={
            "model": "qwen2.5:32b",
            "messages": [
                {
                    "role": "system",
                    "content": instruction
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        },
    )
    return r.json()["choices"][0]["message"]["content"]


def preprocess_response(text):
    """
        Extracts a JSON string from a passage. The JSON string is assumed to
        appear at the end of the passage.

        Parameters:
            text (str): The input text containing the JSON string.

        Returns:
            dict or list: The parsed JSON object if valid, None otherwise.
        """
    try:
        # Find potential JSON strings (starts with { or [ and ends with } or ])
        match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
        if match:
            json_string = match.group(0)
            # Attempt to parse the JSON string
            return json.loads(json_string)
    except json.JSONDecodeError:
        pass
    return None


class Base(ABC):
    hint_path = None

    def __init__(self):

        with open(self.hint_path, mode="r", encoding="utf-8") as f:
            self.system_instruction = f.read()
            self.current_instruction = self.system_instruction

    @abstractmethod
    def construct_question(self, entries):
        pass

    def adjust_instruction(self, entries):
        pass

    def _get_keyword(self, entry):
        return entry.get("word")

    def _get_word_class(self, entry):
        return entry.get("pos")

    def _get_usage(self, entry):
        return entry.get("usage")

    def _get_sense(self, entry):
        return entry.get("definition")

    def _get_context(self, entry):
        return entry.get("labels", "") + entry.get("topic", "")

    def _format_hint_value(self, entry, key, allow_empty=True, value=None):
        if not allow_empty:
            assert bool(value), f'Error {entry.get("id")} has empty {key}'

        if not value:
            return 'None'

        return f'"{value}"'

    @retry(max_retries=4, delay=3)
    def _query_retry(self, entries):
        logger.debug('{} querying qwen', type(self).__name__)
        entries = self.preprocess_entries(entries)
        self.adjust_instruction(entries)
        resp = self._query(entries)
        logger.debug('{}: Response received. {}', type(self).__name__, resp)
        result = preprocess_response(resp)
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
        logger.warning('{}: question: {}', type(self).__name__, question)
        return query_qwen(self.current_instruction, question)

    @abstractmethod
    def _validate(self, result, entries):
        assert isinstance(result, list), "ai response is not a valid list"

        return True

    @abstractmethod
    def preprocess_result(self, results, entries):
        pass

    def preprocess_entries(self, entries):
        return entries


class Translator(Base):
    hint_path = instruction_path / 'translate.txt'

    def preprocess_entries(self, entries):
        assert isinstance(entries, list)
        assert len(entries) == 1
        return format_entry(entries[0])

    def adjust_instruction(self, entry):
        patterns = (
            ("informal", "偏日常随意", "拘谨"),
            ("\bformal\b", "偏正式", "随意"),
            ("ironic", "带讽刺", "太礼貌"),
            ("literary", "文学作品", "较日常"),
            ("old-fashioned", "较老派过时", "较现代"),
            ("old use", "较老派过时", "较现代"),
            ("disapproving", "表达反对", "中立或赞同"),
            ("humorous", "风趣幽默", "较刻板"),
            ("slang", "俚语", "较书面化"),
            ("offensive", "带冒犯", "较礼貌"),
            ("approving", "鼓励赞同", "反对")
        )
        if labels := entry.get("labels"):
            a = []
            b = []
            delimiter = '、'
            for p, ta, tb in patterns:
                if re.search(p, labels):
                    a.append(ta)
                    b.append(tb)

            if len(a) > 1 and 'or' in labels:
                delimiter = '或是'

            self.current_instruction = self.system_instruction.replace('偏口语化', delimiter.join(a)).replace(
                '过于书面化',
                delimiter.join(b)
            )

    def _validate(self, results, entry):
        super()._validate(results, entry)

        assert len(results) == len(
            [x["en"] for x in entry["examples"] if x.get("ai", False)]
        ), "examples length not match"

        for eg in results:
            assert type(eg) is str, 'invalid eg type'

    def construct_question(self, entry):
        header = f'''
            关键词: {self._format_hint_value(entry, 'word', False, value=self._get_keyword(entry))}
            关键词释义: {self._format_hint_value(entry, 'definition', False, value=self._get_sense(entry))}
            需要翻译的句子
            
        '''
        s = [f'{idx + 1}. {x["en"]}' for idx, x in entry["examples"] if x.get("ai", False)]

        return header + '\n'.join(s)

    def preprocess_result(self, results, entry):
        entry = deepcopy(entry)

        ai_egs = list(filter(lambda eg: eg.get("ai", False), entry["examples"]))

        for idx, eg in enumerate(ai_egs):
            eg["cn"] = results[idx]
            # mark as processed
            eg["tld"] = True


        return [
            {
                "id": entry["id"],
                "examples": entry["examples"]
            }
        ]


class Senser(Base):
    hint_path = instruction_path / 'make_example.txt'

    def preprocess_entries(self, entries):
        assert isinstance(entries, list)
        assert len(entries) == 1
        return format_entry(entries[0])

    def construct_question(self, entry):
        return f'''
            keyword: {self._format_hint_value(entry, 'word', False, value=self._get_keyword(entry))}
            usage: {self._format_hint_value(entry, 'usage', True, value=self._get_usage(entry))}
            word class: {self._format_hint_value(entry, 'pos', True, value=self._get_word_class(entry))}
            sense: {self._format_hint_value(entry, 'definition', False, value=self._get_sense(entry))}
            context: {self._format_hint_value(entry, 'context', True, value=self._get_context(entry))}
        '''

    def _validate(self, results, entries):
        super()._validate(results, entries)

        assert len(results) >= 7, 'not making enough examples'

        for eg in results:
            assert type(eg) is str, 'invalid eg type'

    def preprocess_result(self, results, entry):
        examples = copy(entry["examples"])
        if isinstance(examples, list):
            start = len(examples)
        else:
            examples = []
            start = 0
        for idx, eg in enumerate(results):
            examples.append(
                {
                    "en": eg,
                    "cn": "",
                    "name": f'{entry["id"]}_{start + idx}',
                    "ai": True,
                }
            )

        return [
            {
                "id": entry["id"],
                "examples": examples
            }
        ]


def format_entry(entry):
    is_normal_word = "word" in entry

    entry["labels"] = format_labels(entry)
    entry["variants"] = format_variants(entry)
    entry["topic"] = format_topic(entry)

    if is_normal_word:
        entry["word"] = entry.get("variants") or entry.get("word")
        entry["usage"] = format_usage(entry)
    else:
        # idioms or phrvs
        entry["word"] = entry.get("usage")
        entry["usage"] = None

    return entry


def format_usage(entry):
    # "+ adv./prep" -> "<word> + adv./prep"
    usage = entry.get("usage")
    word = entry.get("word")

    if usage and (usage.startswith("+") or usage.startswith("(+")):
        usage = word + ' ' + usage
    return usage


def format_labels(entry):
    # deduplicate
    entry_labels = entry.get("e_labels", "")
    def_labels = entry.get("labels", "")
    if entry_labels and def_labels:
        e_label = re.findall(r'\((.+?)\)', entry_labels)[0]
        d_label = re.findall(r'\((.+?)\)', def_labels)[0]
        if e_label in d_label:
            return f'({e_label})'
        elif d_label in e_label:
            return f'({d_label})'
        else:
            return entry_labels + def_labels

    return entry_labels or def_labels


def format_variants(entry):
    # filter variants like
    # (North American English usually美式英语通常作美式英語通常作 oatmeal)
    # (abbreviation BTW)
    # (often Satanic)

    v = entry.get("variants", "")
    if v.startswith('('):
        return ''
    return v


def format_topic(entry):
    topics = entry.get("topic", "").split("=_=")
    s = ";".join(topics)
    return f'({s})'
