import re
import json
from copy import deepcopy

from tqdm import tqdm
from loguru import logger

from .anki_connect import invoke as anki_invoke
from .models.models import ModelSkills, ModelSynonyms
from ..utils import Recorder

results_recorder = Recorder()


def handle_tag(tag):
    tag = re.sub(r'\band\b', '&', tag)
    tag = re.sub(r'\s+&\s+', '&', tag)
    tag = re.sub(r',\s?', '&', tag)
    return re.sub(r'[\s:]', '_', tag)


class AnkiManager:
    def __init__(self, deck_name):
        self.deck_name = deck_name
        self._create_decks(deck_name)
        self.model = ModelSkills()
        self.synonyms_model = ModelSynonyms()

    def _create_decks(self, deck_name):
        names = [
            deck_name,
            f"{deck_name}::读",
            f"{deck_name}::读::基础",
            f"{deck_name}::读::高频",
            f"{deck_name}::读::高频::普通",  # high-high; mid-high
            f"{deck_name}::读::高频::进阶",  # high-mid
            f"{deck_name}::读::高频::高难",  # high-low
            f"{deck_name}::读::中频",  # mid-mid
            f"{deck_name}::读::低频",
            f"{deck_name}::读::低频::普通",  # low-high
            f"{deck_name}::读::低频::进阶",  # low-mid; mid-low
            f"{deck_name}::读::低频::高难",  # low-low
            f"{deck_name}::读::近义词辨析",
            f"{deck_name}::写",
            f"{deck_name}::写::基础",
            f"{deck_name}::写::高频",
            f"{deck_name}::写::高频::普通",  # high-high; mid-high
            f"{deck_name}::写::高频::进阶",  # high-mid
            f"{deck_name}::写::高频::高难",  # high-low
            f"{deck_name}::写::中频",  # mid-mid
            f"{deck_name}::写::低频",
            f"{deck_name}::写::低频::普通",  # low-high
            f"{deck_name}::写::低频::进阶",  # low-mid; mid-low
            f"{deck_name}::写::低频::高难",  # low-low
            f"{deck_name}::缺省"
        ]
        deck_names = anki_invoke("deckNames")
        for name in names:
            if name not in deck_names:
                anki_invoke("createDeck", deck=name)

    def _get_variant(self, entry):
        variant = entry.get("variants", '')
        return variant if not variant.startswith('(') else None

    def _handle_labels(self, entry):
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

    def handle_examples(self, entry):
        examples = entry["examples"]
        if not examples:
            return ''
        examples = json.loads(examples)
        if not examples:
            return ''

        for eg in examples:
            if usage := eg.get("usage"):
                if variant := self._get_variant(entry):
                    eg["usage"] = usage.replace(variant, '~')
                if word := entry.get("word", ""):
                    eg["usage"] = eg["usage"].replace(word, '~')
            else:
                eg.pop("usage", None)

            if not eg.get("labels", ""):
                eg.pop("labels", None)

            eg.pop("ai", None)
            eg.pop("en_ai", None)

        return json.dumps(examples, ensure_ascii=False)

    def _get_note_fields(self, entry):
        phonetics = entry.get("phonetics", "=_=").split("=_=")
        return {
            "id": entry["id"],
            "word": self._get_variant(entry) or entry.get("word", "") if (
                is_normal_word := "word" in entry) else entry.get("usage", "") or "",
            "BrEPhonetic": phonetics[0],
            "AmEPhonetic": phonetics[1],
            "usage": entry.get("usage", "") if is_normal_word else "" or "",
            "definition": entry["definition"] or "",
            "def_cn": entry["def_cn"] or "",
            "examples": self.handle_examples(entry),
        }

    def _get_categories(self, entry):
        categories = entry.get("topic", "")
        categories = categories.split("=_=") if "=_=" in categories else [categories]
        return [handle_tag(t) for t in categories]

    def _get_tags_from_labels(self, entry):
        labels = entry.get("labels", "") + entry.get("e_labels", "")
        if not labels:
            return []
        replacements = [
            ("North American English", "NAmE"),
            ("Northern British English", "NEngE"),
            ("South African English", "SAfrE"),
            ("East African English", "EAfrE"),
            ("West African English", "WAfrE"),
            ("North African English", "NAfrE"),
            ("South-East Asian English", "SEAsiaE"),
            ("Canadian English", "CanadE"),
            ("Irish English", "IrishE"),
            ("Welsh English", "WelshE"),
            ("Indian English", "IndE"),
            ("Scottish English", "ScotE"),
            ("British English", "BrE"),
            ("US English", "USE"),
            ("African English", "AfrE"),
            ("Australian English", "AustralE"),
            ("New Zealand English", "NZeaE"),
            ("especially", "esp.")
        ]
        for k, v in replacements:
            labels = labels.replace(k, v)

        groups = re.findall(r'\((.+?)\)', labels)

        def process_group(g):
            ls = g.split(", ")
            return [
                f"E_{l.replace(' ', '_')}"
                for l in ls
            ]

        results = [
            item
            for g in groups
            for item in process_group(g)
        ]

        return list(set(results))

    def _get_cefr_tag(self, entry):
        cefr = entry.get("cefr", "")
        if not cefr:
            return []
        return ['CEFR_' + cefr]

    def _get_pos_tag(self, entry):
        pos = entry.get("pos", "")
        if not pos:
            return []

        replacements = [
            ("indefinite article", "IA"),
            ("definite article", "DA"),
            ("ordinal number", "Ord"),
            ("adjective", "adj"),
            ("pronoun", "pron"),
            ("abbreviation", "abbrv"),
            ("phrasal verb", "phrv"),
            ("adverb", "adv"),
            ("conjunction", "conj"),
            ("preposition", "prep"),
        ]

        for k, v in replacements:
            pos = pos.replace(k, v)
        return ['POS_' + handle_tag(t.strip()) for t in pos.split(',')]

    def get_target_deck(self, entry):
        deck_name = self.deck_name

        entry = deepcopy(entry)
        entry["examples"] = json.loads(entry["examples"]) if entry["examples"] else []

        cefr = entry.get('cefr')
        f_sense = entry.get('f_sense')
        f_word = entry.get('f_word')
        examples = entry["examples"]

        if cefr == 'A1' or cefr == 'A2':
            return f"{deck_name}::读::基础"

        if (cefr != 'A1' and cefr != 'A2' and not (f_sense or f_word)) or any([not bool(e["cn"]) for e in examples]):
            return f"{deck_name}::缺省"

        mmap = {
            "HIGH-HIGH": f"{deck_name}::读::高频::普通",
            "HIGH-MEDIUM": f"{deck_name}::读::高频::进阶",
            "HIGH-LOW": f"{deck_name}::读::高频::高难",
            "MEDIUM-HIGH": f"{deck_name}::读::高频::普通",
            "MEDIUM-MEDIUM": f"{deck_name}::读::中频",
            "MEDIUM-LOW": f"{deck_name}::读::低频::进阶",
            "LOW-LOW": f"{deck_name}::读::低频::高难",
            "LOW-HIGH": f"{deck_name}::读::低频::普通",
            "LOW-MEDIUM": f"{deck_name}::读::低频::进阶",
        }
        return mmap[f'{f_sense.upper()}-{f_word.upper()}']

    @logger.catch
    def handle(self, entry):
        note_fields = self._get_note_fields(entry)

        tags = [
            *self._get_categories(entry),
            *self._get_tags_from_labels(entry),
            *self._get_cefr_tag(entry),
            *self._get_pos_tag(entry)
        ]

        deck = self.get_target_deck(entry)

        self.model.add_note(deck, note_fields, tags)

    def handle_synonyms(self, entry):
        tags = ['Synonyms']

        self.synonyms_model.add_note(f"{self.deck_name}::读::近义词辨析", entry, tags)

    def process(self, todos, handle):
        for t in tqdm(todos):
            try:
                handle(t)
            except Exception as e:
                logger.error(e)
                # if 'duplicate' not in str(e):
                #     raise e

    @logger.catch
    def run(self):
        print('adding words to anki...')
        todos = results_recorder.get_all()
        self.process(todos, self.handle)

        print('adding synonyms to anki...')
        synonyms = results_recorder.get_synonyms()
        whichwords = results_recorder.get_whichwords()

        @logger.catch
        def split_syn_entry(entry, typ):
            try:
                entry["defs"] = json.loads(entry["defs"])
                comm = {
                    "words": entry["words"],
                    "overview": entry["overview"] if typ == "Synonyms" else "",
                    "overview_cn": entry["overview_cn"] if typ == "Synonyms" else "",
                    "type": typ
                }
                return [
                    {
                        **comm,
                        "id": d["id"],
                        "definition": d["definition"],
                        "word": d.get("word", ""),
                        "def_cn": d.get("def_cn", ""),
                        "note": d.get("note", ""),
                        "examples": json.dumps(d["examples"], ensure_ascii=False)
                    } for d in entry["defs"]
                ]
            except Exception as e:
                return []

        ss = [
            item
            for e in synonyms
            for item in split_syn_entry(e, "Synonyms")
        ]
        ws = [
            item
            for e in whichwords
            for item in split_syn_entry(e, "Whichwords")
        ]
        self.process([*ss, *ws], self.handle_synonyms)
